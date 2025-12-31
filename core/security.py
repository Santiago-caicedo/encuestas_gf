"""
Utilidades de seguridad para el sistema de encuestas.
"""
import re
import html
from functools import wraps
from django.core.cache import cache
from django.http import HttpResponseForbidden


def sanitize_string(value):
    """
    Sanitiza una cadena para prevenir XSS.
    Escapa caracteres HTML peligrosos.
    """
    if not isinstance(value, str):
        return value

    # Escapar caracteres HTML
    sanitized = html.escape(value, quote=True)

    # Eliminar posibles intentos de inyección de scripts
    # Remover patrones peligrosos comunes
    dangerous_patterns = [
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
        r'on\w+\s*=',  # onclick=, onload=, etc.
    ]

    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

    return sanitized


def sanitize_dict(data, exclude_keys=None):
    """
    Sanitiza todas las cadenas en un diccionario.
    """
    if exclude_keys is None:
        exclude_keys = []

    sanitized = {}
    for key, value in data.items():
        if key in exclude_keys:
            sanitized[key] = value
        elif isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, exclude_keys)
        else:
            sanitized[key] = value

    return sanitized


def validate_hex_color(color):
    """
    Valida que un color sea un código hexadecimal válido.
    Previene CSS injection.
    """
    if not color:
        return '#000000'

    # Patrón para color hex válido: #RGB o #RRGGBB
    hex_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'

    if re.match(hex_pattern, color):
        return color

    # Si no es válido, retornar color por defecto
    return '#000000'


def rate_limit(key_prefix, max_requests=5, window_seconds=60):
    """
    Decorador para limitar la tasa de peticiones.

    Args:
        key_prefix: Prefijo para la clave de cache (ej: 'encuesta')
        max_requests: Número máximo de peticiones permitidas
        window_seconds: Ventana de tiempo en segundos
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Obtener IP del cliente
            ip = get_client_ip(request)
            cache_key = f"rate_limit:{key_prefix}:{ip}"

            # Obtener contador actual
            request_count = cache.get(cache_key, 0)

            if request_count >= max_requests:
                return HttpResponseForbidden(
                    '<h1>Demasiadas solicitudes</h1>'
                    '<p>Has excedido el límite de envíos. Por favor espera unos minutos antes de intentar nuevamente.</p>'
                )

            # Incrementar contador
            cache.set(cache_key, request_count + 1, window_seconds)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_client_ip(request):
    """
    Obtiene la IP real del cliente, considerando proxies.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Tomar la primera IP (la del cliente original)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


class LoginRateLimiter:
    """
    Limitador de intentos de login para prevenir fuerza bruta.
    """
    MAX_ATTEMPTS = 5
    LOCKOUT_TIME = 300  # 5 minutos en segundos

    @classmethod
    def get_cache_key(cls, identifier):
        return f"login_attempts:{identifier}"

    @classmethod
    def is_locked(cls, identifier):
        """Verifica si el identificador está bloqueado."""
        cache_key = cls.get_cache_key(identifier)
        attempts = cache.get(cache_key, {'count': 0, 'locked': False})
        return attempts.get('locked', False)

    @classmethod
    def record_attempt(cls, identifier, success=False):
        """Registra un intento de login."""
        cache_key = cls.get_cache_key(identifier)
        attempts = cache.get(cache_key, {'count': 0, 'locked': False})

        if success:
            # Login exitoso: resetear contador
            cache.delete(cache_key)
            return

        # Login fallido: incrementar contador
        attempts['count'] += 1

        if attempts['count'] >= cls.MAX_ATTEMPTS:
            attempts['locked'] = True
            cache.set(cache_key, attempts, cls.LOCKOUT_TIME)
        else:
            cache.set(cache_key, attempts, cls.LOCKOUT_TIME)

    @classmethod
    def get_remaining_attempts(cls, identifier):
        """Obtiene los intentos restantes."""
        cache_key = cls.get_cache_key(identifier)
        attempts = cache.get(cache_key, {'count': 0, 'locked': False})
        return max(0, cls.MAX_ATTEMPTS - attempts['count'])
