from django.urls import path

from .views import RegisterView, PasswordResetRequestView, PasswordResetConfirmView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='account-register'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
