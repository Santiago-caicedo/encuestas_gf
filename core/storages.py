# core/storages.py
from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class StaticStorage(S3Boto3Storage):
    """
    Guarda los archivos estáticos (CSS, JS, Imágenes del sistema)
    en la ruta: s3://vadomdata/{S3_CLIENT_PREFIX}/static/
    """
    location = f'{settings.S3_CLIENT_PREFIX}/static'
    default_acl = None  # Importante: Desactiva ACLs

class MediaStorage(S3Boto3Storage):
    """
    Guarda los archivos subidos por usuarios (Logos, adjuntos)
    en la ruta: s3://vadomdata/{S3_CLIENT_PREFIX}/media/
    """
    location = f'{settings.S3_CLIENT_PREFIX}/media'
    default_acl = None
    file_overwrite = False  # No sobrescribir archivos con el mismo nombre