from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Send a test email using the configured email backend (use --to to set recipients)'

    def add_arguments(self, parser):
        parser.add_argument('--to', nargs='+', type=str, default=['edetd8326@gmail.com'],
                            help='Recipient email addresses')
        parser.add_argument('--subject', type=str, default='Test email from Django')
        parser.add_argument('--message', type=str, default='This is a test email sent from the management command.')

    def handle(self, *args, **options):
        to = options['to']
        subject = options['subject']
        message = options['message']
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or None

        try:
            sent = send_mail(subject, message, from_email, to, fail_silently=False)
            self.stdout.write(self.style.SUCCESS(f'Emails sent: {sent}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error sending email: {e}'))
