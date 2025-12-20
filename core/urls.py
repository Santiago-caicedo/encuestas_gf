from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- AUTENTICACIÓN ---
    # Login personalizado
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
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