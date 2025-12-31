from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .auth_views import SecureLoginView

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- AUTENTICACIÓN ---
    # Login con protección anti brute-force
    path('accounts/login/', SecureLoginView.as_view(), name='login'),
    # Resto de funciones de auth (logout, password reset, etc)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # --- APLICACIONES ---
    # 1. Formularios Públicos (encuestas)
    # Lo ponemos antes para asegurar que /encuesta/ siga funcionando
    path('', include('formularios.urls')),

    # 2. Dashboard en la RAÍZ
    # Al ponerlo en '' (vacío), el dashboard_home se vuelve la página de inicio
    path('', include('dashboard.urls')), 
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)