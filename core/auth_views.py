"""
Vistas de autenticación con seguridad mejorada.
"""
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import redirect
from .security import LoginRateLimiter, get_client_ip


class SecureLoginView(LoginView):
    """
    Vista de login con protección contra ataques de fuerza bruta.
    """
    template_name = 'registration/login.html'

    def get_rate_limit_identifier(self):
        """Obtiene un identificador único para el rate limiting."""
        # Usamos la IP del cliente
        return get_client_ip(self.request)

    def get(self, request, *args, **kwargs):
        identifier = self.get_rate_limit_identifier()

        # Verificar si está bloqueado
        if LoginRateLimiter.is_locked(identifier):
            messages.error(
                request,
                'Tu cuenta ha sido bloqueada temporalmente debido a demasiados intentos fallidos. '
                'Por favor, espera 5 minutos antes de intentar nuevamente.'
            )

        return super().get(request, *args, **kwargs)

    def form_invalid(self, form):
        """Se llama cuando el login falla."""
        identifier = self.get_rate_limit_identifier()

        # Registrar intento fallido
        LoginRateLimiter.record_attempt(identifier, success=False)

        # Verificar si ahora está bloqueado
        if LoginRateLimiter.is_locked(identifier):
            messages.error(
                self.request,
                'Has excedido el número máximo de intentos. '
                'Tu acceso ha sido bloqueado por 5 minutos.'
            )
        else:
            remaining = LoginRateLimiter.get_remaining_attempts(identifier)
            if remaining <= 3:
                messages.warning(
                    self.request,
                    f'Credenciales incorrectas. Te quedan {remaining} intentos antes del bloqueo temporal.'
                )

        return super().form_invalid(form)

    def form_valid(self, form):
        """Se llama cuando el login es exitoso."""
        identifier = self.get_rate_limit_identifier()

        # Verificar si está bloqueado (por si intenta manipular)
        if LoginRateLimiter.is_locked(identifier):
            messages.error(
                self.request,
                'Tu acceso está temporalmente bloqueado. Por favor espera unos minutos.'
            )
            return redirect('login')

        # Limpiar intentos fallidos
        LoginRateLimiter.record_attempt(identifier, success=True)

        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        """Intercepta POST para verificar bloqueo antes de procesar."""
        identifier = self.get_rate_limit_identifier()

        # Verificar si está bloqueado antes de procesar
        if LoginRateLimiter.is_locked(identifier):
            messages.error(
                request,
                'Tu acceso está temporalmente bloqueado debido a demasiados intentos fallidos. '
                'Por favor espera 5 minutos.'
            )
            return redirect('login')

        return super().post(request, *args, **kwargs)
