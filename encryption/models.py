from django.db import models
from django.contrib.auth.models import User

class EncryptionKey(models.Model):
    key_name = models.CharField(max_length=100, unique=True)
    key_value = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.key_name

class EncryptedData(models.Model):
    data_name = models.CharField(max_length=100)
    encrypted_value = models.TextField()
    key = models.ForeignKey(EncryptionKey, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.data_name

class EncryptedFile(models.Model):
    file_name = models.CharField(max_length=255)
    encrypted_file = models.FileField(upload_to='media/encrypted_files/')
    key = models.ForeignKey(EncryptionKey, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

class TwoFactorCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    def __str__(self):
        return f"2FA for {self.user.username} - used={self.used}"
