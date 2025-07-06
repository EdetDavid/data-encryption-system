from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .models import EncryptionKey, EncryptedData, EncryptedFile
from cryptography.fernet import Fernet
import os
from django.db import IntegrityError

def generate_key(request):
    if request.method == 'POST':
        key_name = request.POST.get('key_name')
        if key_name:
            key_value = Fernet.generate_key().decode()
            try:
                EncryptionKey.objects.create(key_name=key_name, key_value=key_value)
                return render(request, 'encryption/generate_key.html', {'key_value': key_value})
            except IntegrityError:
                # Use Django messages framework for modal error
                from django.contrib import messages
                messages.error(request, f"Key name '{key_name}' already exists. Please choose a different name.")
                return render(request, 'encryption/generate_key.html')
    return render(request, 'encryption/generate_key.html')

def encrypt_data(request):
    if request.method == 'POST':
        data_name = request.POST.get('data_name')
        data_value = request.POST.get('data_value')
        key_name = request.POST.get('key_name')

        if data_name and data_value and key_name:
            try:
                key = EncryptionKey.objects.get(key_name=key_name)
                fernet = Fernet(key.key_value.encode())
                encrypted_value = fernet.encrypt(data_value.encode()).decode()
                EncryptedData.objects.create(data_name=data_name, encrypted_value=encrypted_value, key=key)
                return render(request, 'encryption/encrypt_data.html', {'encrypted_value': encrypted_value})
            except EncryptionKey.DoesNotExist:
                return render(request, 'encryption/encrypt_data.html', {'error': 'Key not found'})
    return render(request, 'encryption/encrypt_data.html')

def decrypt_data(request):
    if request.method == 'POST':
        data_name = request.POST.get('data_name')
        key_name = request.POST.get('key_name')

        if data_name and key_name:
            try:
                key = EncryptionKey.objects.get(key_name=key_name)
                data = EncryptedData.objects.get(data_name=data_name, key=key)
                fernet = Fernet(key.key_value.encode())
                decrypted_value = fernet.decrypt(data.encrypted_value.encode()).decode()
                return render(request, 'encryption/decrypt_data.html', {'decrypted_value': decrypted_value})
            except (EncryptionKey.DoesNotExist, EncryptedData.DoesNotExist):
                return render(request, 'encryption/decrypt_data.html', {'error': 'Key or data not found'})
    return render(request, 'encryption/decrypt_data.html')

# File Encryption View
def encrypt_file(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        key_name = request.POST.get('key_name')

        if key_name:
            try:
                key = EncryptionKey.objects.get(key_name=key_name)
                fernet = Fernet(key.key_value.encode())

                # Encrypt file content
                encrypted_content = fernet.encrypt(file.read())

                # Save encrypted file to media directory
                encrypted_file_path = os.path.join(settings.MEDIA_ROOT, 'encrypted_files', file.name)
                os.makedirs(os.path.dirname(encrypted_file_path), exist_ok=True)
                with open(encrypted_file_path, 'wb') as f:
                    f.write(encrypted_content)

                # Save file record in the database
                encrypted_file_instance = EncryptedFile.objects.create(
                    file_name=file.name,
                    encrypted_file=f'encrypted_files/{file.name}',
                    key=key
                )

                return render(request, 'encryption/encrypt_file.html', {'message': 'File encrypted successfully'})
            except EncryptionKey.DoesNotExist:
                return render(request, 'encryption/encrypt_file.html', {'error': 'Key not found'})
    return render(request, 'encryption/encrypt_file.html')

# File Decryption View
def decrypt_file(request):
    if request.method == 'POST':
        file_name = request.POST.get('file_name')
        key_name = request.POST.get('key_name')

        if file_name and key_name:
            try:
                key = EncryptionKey.objects.get(key_name=key_name)
                encrypted_file_instance = EncryptedFile.objects.get(file_name=file_name, key=key)
                fernet = Fernet(key.key_value.encode())

                # Read encrypted file content
                encrypted_file_path = os.path.join(settings.MEDIA_ROOT, encrypted_file_instance.encrypted_file.name)
                with open(encrypted_file_path, 'rb') as f:
                    encrypted_content = f.read()

                # Decrypt file content
                decrypted_content = fernet.decrypt(encrypted_content)

                # Save decrypted file to media directory
                decrypted_file_path = os.path.join(settings.MEDIA_ROOT, 'decrypted_files', file_name)
                os.makedirs(os.path.dirname(decrypted_file_path), exist_ok=True)
                with open(decrypted_file_path, 'wb') as f:
                    f.write(decrypted_content)

                return render(request, 'encryption/decrypt_file.html', {
                    'message': 'File decrypted successfully',
                    'file_path': f'decrypted_files/{file_name}',
                    'decrypted_file_url': settings.MEDIA_URL + f'decrypted_files/{file_name}'
                })
            except (EncryptionKey.DoesNotExist, EncryptedFile.DoesNotExist):
                return render(request, 'encryption/decrypt_file.html', {'error': 'Key or file not found'})
    return render(request, 'encryption/decrypt_file.html')

def record_system(request):
    keys = EncryptionKey.objects.all()
    encrypted_files = EncryptedFile.objects.all()
    return render(request, 'encryption/record_system.html', {
        'keys': keys,
        'encrypted_files': encrypted_files
    })
