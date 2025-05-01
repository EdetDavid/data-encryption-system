from django.urls import path
from . import views

urlpatterns = [
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