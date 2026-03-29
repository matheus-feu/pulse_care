"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.swagger import (
    AUTH_TOKEN_REQUEST_SERIALIZER,
    AUTH_TOKEN_RESPONSE_SERIALIZER,
    TOKEN_REFRESH_REQUEST_SERIALIZER,
    TOKEN_REFRESH_RESPONSE_SERIALIZER,
    extend_schema_with_examples,
    request_example,
    response_example,
)

TokenObtainPairView = extend_schema_with_examples(
    tags=['Auth'],
    summary='Obtain JWT access & refresh tokens',
    description='Authenticate with **email + password** and receive a JWT access token (8 h) and refresh token (7 d).',
    request=AUTH_TOKEN_REQUEST_SERIALIZER,
    responses={200: AUTH_TOKEN_RESPONSE_SERIALIZER},
    request_examples=[
        request_example(
            'Login request',
            {
                'email': 'email@email.com',
                'password': 'Senha@123',
            },
        ),
    ],
    response_examples=[
        response_example(
            'Login success',
            {
                'refresh': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh-token',
                'access': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access-token',
            },
            status_codes=200,
        ),
    ],
)(TokenObtainPairView)

TokenRefreshView = extend_schema_with_examples(
    tags=['Auth'],
    summary='Refresh the JWT access token',
    description='Exchange a valid refresh token for a new access token.',
    request=TOKEN_REFRESH_REQUEST_SERIALIZER,
    responses={200: TOKEN_REFRESH_RESPONSE_SERIALIZER},
    request_examples=[
        request_example(
            'Refresh request',
            {
                'refresh': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh-token',
            },
        ),
    ],
    response_examples=[
        response_example(
            'Refresh success',
            {
                'access': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.new-access-token',
            },
            status_codes=200,
        ),
    ],
)(TokenRefreshView)

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
                  path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
                  path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
                  path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
                  path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
                  path('api/accounts/', include('apps.accounts.urls')),
                  path('api/users/', include('apps.users.urls')),
                  path('api/patients/', include('apps.patients.urls')),
                  path('api/appointments/', include('apps.appointments.urls')),
                  path('api/records/', include('apps.records.urls')),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
