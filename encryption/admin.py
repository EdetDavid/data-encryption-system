from django.contrib import admin
from .models import EncryptionKey, EncryptedData, EncryptedFile, TwoFactorCode


@admin.register(EncryptionKey)
class EncryptionKeyAdmin(admin.ModelAdmin):
	list_display = ('key_name', 'user', 'created_at')
	search_fields = ('key_name', 'user__username')
	readonly_fields = ('created_at',)


@admin.register(EncryptedData)
class EncryptedDataAdmin(admin.ModelAdmin):
	list_display = ('data_name', 'user', 'key', 'created_at')
	search_fields = ('data_name', 'user__username', 'key__key_name')
	list_filter = ('user',)
	readonly_fields = ('created_at',)


@admin.register(EncryptedFile)
class EncryptedFileAdmin(admin.ModelAdmin):
	list_display = ('file_name', 'user', 'key', 'created_at')
	search_fields = ('file_name', 'user__username')
	readonly_fields = ('created_at',)


@admin.register(TwoFactorCode)
class TwoFactorCodeAdmin(admin.ModelAdmin):
	list_display = ('user', 'code', 'used', 'attempts', 'created_at')
	search_fields = ('user__username', 'code')
	list_filter = ('used',)
	readonly_fields = ('created_at',)
