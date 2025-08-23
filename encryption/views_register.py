from __future__ import annotations

"""
File: encryption/views_register.py
Fix: Make Resend email sending reliable, with rich diagnostics and SMTP fallback.
"""
from typing import Optional, Dict, Any
import os
import random
import datetime
import logging
import json
import smtplib

# Optional requests import for HTTP fallback to Resend
try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

from django.shortcuts import render, redirect
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# Optional Resend SDK import
try:
    import resend  # type: ignore
except Exception:  # pragma: no cover
    resend = None  # type: ignore

logger = logging.getLogger(__name__)


# -------- Email helpers ----------------------------------------------------

def _format_email_content(username: str, code: str) -> Dict[str, str]:
    subject = "Data Security System - Login Verification Code"
    text = (
        f"Hello {username},\n\n"
        f"Your verification code for Data Security System login is: {code}\n\n"
        "This code will expire in 10 minutes for security reasons.\n\n"
        "If you didn't request this code, please ignore this email.\n\n"
        "Best regards,\nData Security System Team"
    )
    html = (
        f"<p>Hello {username},</p>"
        f"<p>Your verification code for <strong>Data Security System</strong> login is: "
        f'<strong style="letter-spacing:2px">{code}</strong></p>'
        "<p>This code will expire in <strong>10 minutes</strong> for security reasons.</p>"
        "<p>If you didn't request this code, please ignore this email.</p>"
        "<p>Best regards,<br/>Data Security System Team</p>"
    )
    return {"subject": subject, "text": text, "html": html}


def _log_exception(prefix: str, exc: Exception) -> None:
    """Log as much as we can about third‑party errors.
    Why: Your log showed "Unknown error" which hides root cause.
    """
    # Generic details
    details = getattr(exc, "message", None) or ", ".join(str(a) for a in getattr(exc, "args", []) if a) or str(exc)
    logger.warning("%s (%s): %s", prefix, type(exc).__name__, details)

    # Attempt to extract HTTP response info exposed by SDKs
    resp = getattr(exc, "response", None)
    if resp is not None:
        try:
            body = resp.json()
        except Exception:
            body = getattr(resp, "text", "<no text>")
        logger.warning("%s response: status=%s body=%s", prefix, getattr(resp, "status_code", "?"), body)


def _send_via_resend(to_email: str, subject: str, text: str, html: str) -> bool:
    api_key: Optional[str] = getattr(settings, "RESEND_API_KEY", None) or os.environ.get("RESEND_API_KEY")
    from_addr = getattr(settings, "DEFAULT_FROM_EMAIL", "onboarding@resend.dev")
    # Optional test recipient to use when Resend account is in testing mode
    test_recipient = getattr(settings, "RESEND_TEST_RECIPIENT", None) or os.environ.get("RESEND_TEST_RECIPIENT")
    test_from = getattr(settings, "RESEND_TEST_FROM", None) or os.environ.get("RESEND_TEST_FROM")

    if resend is None or not api_key:
        return False

    try:
        resend.api_key = api_key
        # SDK expects dict payload; returns id dict on success
        payload: Dict[str, Any] = {
            "from": from_addr,
            "to": [to_email],
            "subject": subject,
            "text": text,
            "html": html,
        }
        result = resend.Emails.send(payload)
        logger.info("Resend send ok: %s", result)
        return True
    except Exception as exc:  # keep login path alive
        _log_exception("Resend SDK send failed", exc)

        # Try HTTP API fallback if requests is available
        if not requests:
            logger.warning("requests library not available; cannot use HTTP fallback for Resend")
            return False

        try:
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "from": from_addr,
                "to": [to_email],
                "subject": subject,
                "text": text,
                "html": html,
            }
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
            try:
                body = resp.json()
            except Exception:
                body = resp.text

            if resp.status_code in (200, 201):
                logger.info("Resend HTTP send ok: status=%s body=%s", resp.status_code, body)
                return True

            # If Resend is in testing mode it often returns 403/422 and only allows sending to the account owner.
            # If a test recipient is configured, retry using that address as both from and to.
            logger.warning("Resend HTTP send failed: status=%s body=%s", resp.status_code, body)
            if test_recipient and (resp.status_code in (401, 403, 422) or (isinstance(body, dict) and body.get("error"))):
                logger.info("Retrying Resend HTTP using test recipient=%s", test_recipient)
                retry_from = test_from or test_recipient
                payload_retry = {
                    "from": retry_from,
                    "to": [test_recipient],
                    "subject": subject,
                    "text": text,
                    "html": html,
                }
                try:
                    resp2 = requests.post(url, headers=headers, data=json.dumps(payload_retry), timeout=10)
                    try:
                        body2 = resp2.json()
                    except Exception:
                        body2 = resp2.text
                    if resp2.status_code in (200, 201):
                        logger.info("Resend HTTP retry ok: status=%s body=%s", resp2.status_code, body2)
                        return True
                    logger.warning("Resend HTTP retry failed: status=%s body=%s", resp2.status_code, body2)
                except Exception as exc3:
                    _log_exception("Resend HTTP retry failed", exc3)

            return False
        except Exception as exc2:
            _log_exception("Resend HTTP fallback failed", exc2)
            return False
                

def _send_via_brevo_api(to_email: str, subject: str, text: str, html: str) -> bool:
    """Send email through Brevo (Sendinblue) REST API using BREVO_API_KEY.
    This is HTTPS-based so it works on hosts that block SMTP (for example PythonAnywhere free).
    """
    api_key = getattr(settings, 'BREVO_API_KEY', None) or os.environ.get('BREVO_API_KEY')
    if not api_key:
        return False
    if not requests:
        logger.warning("requests not available; cannot use Brevo REST API")
        return False

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        'api-key': api_key,
        'Content-Type': 'application/json',
    }
    payload = {
        'sender': {'email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'onboarding@resend.dev').split('<')[-1].strip('>') , 'name': getattr(settings, 'DEFAULT_FROM_EMAIL', 'Data Security').split('<')[0].strip()},
        'to': [{'email': to_email}],
        'subject': subject,
        'textContent': text,
        'htmlContent': html,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        if resp.status_code in (200, 201, 202):
            logger.info("Brevo API send ok: status=%s body=%s", resp.status_code, body)
            return True
        logger.warning("Brevo API send failed: status=%s body=%s", resp.status_code, body)
        return False
    except Exception as exc:
        _log_exception("Brevo API send failed", exc)
        return False


def _send_via_smtp(to_email: str, subject: str, text: str) -> bool:
    from_addr = getattr(settings, "DEFAULT_FROM_EMAIL", "onboarding@resend.dev")
    try:
        # fail_silently=False so we can see real SMTP errors in logs
        sent = send_mail(subject, text, from_addr, [to_email], fail_silently=False)
        logger.info("SMTP send ok: %s", bool(sent))
        return bool(sent)
    except Exception as exc:
        _log_exception("SMTP send_mail failed", exc)
        return False


def _send_verification_email(*, to_email: str, username: str, code: str) -> None:
    content = _format_email_content(username, code)

    # Prefer Resend SDK; fall back to SMTP if needed
    if _send_via_resend(to_email, content["subject"], content["text"], content["html"]):
        return
    # Try Brevo REST API (HTTPS) next - works when SMTP is blocked
    if _send_via_brevo_api(to_email, content["subject"], content["text"], content["html"]):
        return
    if _send_via_smtp(to_email, content["subject"], content["text"]):
        return

    # Final fallback for development: log the OTP so testing can continue.
    logger.warning("All email delivery methods failed; falling back to console. OTP for %s is: %s", to_email, code)
    # Also print to stdout so developers running runserver see it immediately
    print(f"[DEV OTP] user={username} email={to_email} code={code}")


# -------- Auth views -------------------------------------------------------

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        email = request.POST.get('email', '').strip()
        if not email:
            return render(request, "encryption/registration/register.html", {"form": form, "error": "Email is required."})

        User = get_user_model()
        if User.objects.filter(email__iexact=email).exists():
            return render(request, "encryption/registration/register.html", {"form": form, "error": "Email already in use."})

        if form.is_valid():
            user = form.save(commit=False)
            user.email = email
            user.save()
            auth_login(request, user)
            return redirect("dashboard")
    else:
        form = UserCreationForm()
    return render(request, "encryption/registration/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.email:
                return render(
                    request,
                    "encryption/registration/login.html",
                    {"form": form, "error": "No email on your account; contact admin."},
                )

            code = f"{random.randint(0, 999_999):06d}"
            request.session["pre_2fa_user_id"] = user.id
            request.session["pre_2fa_code"] = code
            request.session["pre_2fa_expires"] = (timezone.now() + datetime.timedelta(minutes=10)).timestamp()

            _send_verification_email(to_email=user.email, username=user.username, code=code)
            return redirect("verify_2fa")
    else:
        form = AuthenticationForm()
    return render(request, "encryption/registration/login.html", {"form": form})


def logout_view(request):
    auth_logout(request)
    return redirect("custom_login")


def verify_2fa(request):
    if request.method == "POST":
        code = request.POST.get("code")
        stored_code = request.session.get("pre_2fa_code")
        user_id = request.session.get("pre_2fa_user_id")
        expires_ts = request.session.get("pre_2fa_expires")

        if not (stored_code and user_id and expires_ts):
            return redirect("custom_login")

        if timezone.now().timestamp() > float(expires_ts):
            request.session.pop("pre_2fa_code", None)
            request.session.pop("pre_2fa_user_id", None)
            request.session.pop("pre_2fa_expires", None)
            return render(request, "encryption/registration/verify_2fa.html", {"error": "Code expired. Please login again."})

        if code == stored_code:
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return redirect("custom_login")

            auth_login(request, user)
            request.session.pop("pre_2fa_code", None)
            request.session.pop("pre_2fa_user_id", None)
            request.session.pop("pre_2fa_expires", None)
            return redirect("dashboard")
        else:
            return render(request, "encryption/registration/verify_2fa.html", {"error": "Invalid code."})

    return render(request, "encryption/registration/verify_2fa.html")
