from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .models import EncryptionKey, EncryptedData, EncryptedFile
from cryptography.fernet import Fernet
import os
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages


@login_required
def generate_key(request):
    if request.method == "POST":
        key_name = request.POST.get("key_name")
        if key_name:
            key_value = Fernet.generate_key().decode()
            try:
                EncryptionKey.objects.create(
                    key_name=key_name, key_value=key_value, user=request.user
                )
                return render(
                    request,
                    "encryption/generate_key.html",
                    {"key_value": key_value, "success": True},
                )
            except IntegrityError:
                messages.error(
                    request,
                    f"Key name '{key_name}' already exists. Please choose a different name.",
                )
    return render(request, "encryption/generate_key.html")


@login_required
def encrypt_data(request):
    if request.method == "POST":
        data_name = request.POST.get("data_name")
        data_value = request.POST.get("data_value")
        key_name = request.POST.get("key_name")
        user = request.user
        if data_name and data_value and key_name:
            try:
                key = EncryptionKey.objects.get(key_name=key_name)
                fernet = Fernet(key.key_value.encode())
                encrypted_value = fernet.encrypt(data_value.encode()).decode()
                EncryptedData.objects.create(
                    data_name=data_name,
                    encrypted_value=encrypted_value,
                    key=key,
                    user=user,
                )
                return render(
                    request,
                    "encryption/encrypt_data.html",
                    {"encrypted_value": encrypted_value},
                )
            except EncryptionKey.DoesNotExist:
                return render(
                    request, "encryption/encrypt_data.html", {"error": "Key not found"}
                )
    return render(request, "encryption/encrypt_data.html")


@login_required
def decrypt_data(request):
    if request.method == "POST":
        data_name = request.POST.get("data_name")
        key_name = request.POST.get("key_name")

        if data_name and key_name:
            try:
                key = EncryptionKey.objects.get(key_name=key_name)
                data = EncryptedData.objects.get(data_name=data_name, key=key)
                fernet = Fernet(key.key_value.encode())
                decrypted_value = fernet.decrypt(data.encrypted_value.encode()).decode()
                return render(
                    request,
                    "encryption/decrypt_data.html",
                    {"decrypted_value": decrypted_value},
                )
            except (EncryptionKey.DoesNotExist, EncryptedData.DoesNotExist):
                return render(
                    request,
                    "encryption/decrypt_data.html",
                    {"error": "Key or data not found"},
                )
    return render(request, "encryption/decrypt_data.html")


# File Encryption View
@login_required
def encrypt_file(request):
    if request.method == "POST" and request.FILES["file"]:
        file = request.FILES["file"]
        key_name = request.POST.get("key_name")
        user = request.user

        if key_name:
            try:
                key = EncryptionKey.objects.get(key_name=key_name)
                fernet = Fernet(key.key_value.encode())

                # Encrypt file content
                encrypted_content = fernet.encrypt(file.read())

                # Save encrypted file to media directory
                encrypted_file_path = os.path.join(
                    settings.MEDIA_ROOT, "encrypted_files", file.name
                )
                os.makedirs(os.path.dirname(encrypted_file_path), exist_ok=True)
                with open(encrypted_file_path, "wb") as f:
                    f.write(encrypted_content)

                # Save file record in the database
                encrypted_file_instance = EncryptedFile.objects.create(
                    file_name=file.name,
                    encrypted_file=f"encrypted_files/{file.name}",
                    key=key,
                    user=user,
                )

                return render(
                    request,
                    "encryption/encrypt_file.html",
                    {"message": "File encrypted successfully"},
                )
            except EncryptionKey.DoesNotExist:
                return render(
                    request, "encryption/encrypt_file.html", {"error": "Key not found"}
                )
    return render(request, "encryption/encrypt_file.html")


# File Decryption View
@login_required
def decrypt_file(request):
    if request.method == "POST":
        file_name = request.POST.get("file_name")
        key_name = request.POST.get("key_name")

        if file_name and key_name:
            try:
                key = EncryptionKey.objects.get(key_name=key_name)
                encrypted_file_instance = EncryptedFile.objects.get(
                    file_name=file_name, key=key
                )
                fernet = Fernet(key.key_value.encode())

                # Read encrypted file content
                encrypted_file_path = os.path.join(
                    settings.MEDIA_ROOT, encrypted_file_instance.encrypted_file.name
                )
                with open(encrypted_file_path, "rb") as f:
                    encrypted_content = f.read()

                # Decrypt file content
                decrypted_content = fernet.decrypt(encrypted_content)

                # Save decrypted file to media directory
                decrypted_file_path = os.path.join(
                    settings.MEDIA_ROOT, "decrypted_files", file_name
                )
                os.makedirs(os.path.dirname(decrypted_file_path), exist_ok=True)
                with open(decrypted_file_path, "wb") as f:
                    f.write(decrypted_content)

                return render(
                    request,
                    "encryption/decrypt_file.html",
                    {
                        "message": "File decrypted successfully",
                        "file_path": f"decrypted_files/{file_name}",
                        "decrypted_file_url": settings.MEDIA_URL
                        + f"decrypted_files/{file_name}",
                    },
                )
            except (EncryptionKey.DoesNotExist, EncryptedFile.DoesNotExist):
                return render(
                    request,
                    "encryption/decrypt_file.html",
                    {"error": "Key or file not found"},
                )
    return render(request, "encryption/decrypt_file.html")


@login_required
def record_system(request):
    keys = EncryptionKey.objects.all()
    encrypted_files = EncryptedFile.objects.all()
    return render(
        request,
        "encryption/record_system.html",
        {"keys": keys, "encrypted_files": encrypted_files},
    )


@login_required
def dashboard(request):
    # Only show data related to the current logged-in user
    key_count = EncryptionKey.objects.filter(user=request.user).count()
    file_count = EncryptedFile.objects.filter(user=request.user).count()
    data_count = EncryptedData.objects.filter(user=request.user).count()
    latest_key = EncryptionKey.objects.filter(user=request.user).order_by("-id").first()
    latest_file = EncryptedFile.objects.filter(user=request.user).order_by("-id").first()
    latest_data = EncryptedData.objects.filter(user=request.user).order_by("-id").first()
    user_keys = EncryptionKey.objects.filter(user=request.user)
    user_files = EncryptedFile.objects.filter(user=request.user)
    user_data = EncryptedData.objects.filter(user=request.user)
    return render(
        request,
        "encryption/dashboard.html",
        {
            "key_count": key_count,
            "file_count": file_count,
            "data_count": data_count,
            "latest_key": latest_key,
            "latest_file": latest_file,
            "latest_data": latest_data,
            "user_keys": user_keys,
            "user_files": user_files,
            "user_data": user_data,
        },
    )


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect(
            "generate_key"
        )  # Change to your main app view name if different
    else:
        return redirect("login")


@staff_member_required
def custom_admin_panel(request):
    user_count = User.objects.count()
    file_count = EncryptedFile.objects.count()
    key_count = EncryptionKey.objects.count()
    users = User.objects.all()
    keys = EncryptionKey.objects.all()
    encrypted_files = EncryptedFile.objects.all()
    encrypted_data = EncryptedData.objects.all()
    # More details for dashboard
    staff_count = User.objects.filter(is_staff=True).count()
    superuser_count = User.objects.filter(is_superuser=True).count()
    latest_user = User.objects.order_by("-date_joined").first()
    latest_file = EncryptedFile.objects.order_by("-id").first()
    latest_key = EncryptionKey.objects.order_by("-id").first()
    return render(
        request,
        "encryption/admin_panel.html",
        {
            "user_count": user_count,
            "file_count": file_count,
            "key_count": key_count,
            "users": users,
            "keys": keys,
            "encrypted_files": encrypted_files,
            "encrypted_data": encrypted_data,
            "staff_count": staff_count,
            "superuser_count": superuser_count,
            "latest_user": latest_user,
            "latest_file": latest_file,
            "latest_key": latest_key,
        },
    )


@login_required
def delete_encrypted_file(request, file_id):
    try:
        file_instance = EncryptedFile.objects.get(id=file_id)
        file_instance.delete()
        messages.success(request, "File deleted successfully.")
    except EncryptedFile.DoesNotExist:
        messages.error(request, "File not found.")
    return redirect('record_system')
