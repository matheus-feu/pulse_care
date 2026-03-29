from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicalRecordViewSet, RecordAttachmentViewSet

router = DefaultRouter()
router.register(r'', MedicalRecordViewSet, basename='record')
router.register(r'attachments', RecordAttachmentViewSet, basename='record-attachment')

urlpatterns = [
    path('', include(router.urls)),
]

