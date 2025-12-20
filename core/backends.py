from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailBackend(ModelBackend):
    """
    Permite iniciar sesión con username O con email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Buscamos un usuario cuyo username O email coincida con lo que escribieron
            user = UserModel.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            return None
        except UserModel.MultipleObjectsReturned:
            # Si por error hay correos duplicados, tomamos el primero
            user = UserModel.objects.filter(email__iexact=username).order_by('id').first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None