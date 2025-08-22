from django.urls import path
from . import views
from . import views_register
from .views import delete_encrypted_file

urlpatterns = [
    path('', views.root_redirect, name='root_redirect'),
    path('generate-key/', views.generate_key, name='generate_key'),
    path('encrypt-data/', views.encrypt_data, name='encrypt_data'),
    path('decrypt-data/', views.decrypt_data, name='decrypt_data'),
]

urlpatterns += [
    path('encrypt-file/', views.encrypt_file, name='encrypt_file'),
    path('decrypt-file/', views.decrypt_file, name='decrypt_file'),
]

urlpatterns += [
    path('records/', views.record_system, name='record_system'),
]

urlpatterns += [
    path('register/', views_register.register, name='register'),
    path('login/', views_register.login_view, name='custom_login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-panel/', views.custom_admin_panel, name='custom_admin_panel'),
    path('logout/', views_register.logout_view, name='logout'),
]

urlpatterns += [
    path('delete-file/<int:file_id>/', delete_encrypted_file, name='delete_encrypted_file'),
    path('verify-2fa/', views_register.verify_2fa, name='verify_2fa'),
]