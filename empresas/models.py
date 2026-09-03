from django.db import models


class EmpresaClienteQuerySet(models.QuerySet):
    def visibles_para(self, user):
        """Oculta las empresas marcadas 'solo superadmin' a quien no lo sea."""
        if user.is_superuser:
            return self
        return self.exclude(solo_superadmin=True)


class EmpresaCliente(models.Model):

    # Opciones para el selector
    OPCIONES_ALIADO = [
        ('GFR', 'Gestión Financiera de Riesgos'),
        ('LEGAL_SHIELD', 'Legal Shield'),
    ]

    nombre = models.CharField(max_length=255, verbose_name="Nombre de la Empresa")
    slug = models.SlugField(unique=True, help_text="Identificador único para la URL")

    aliado = models.CharField(
        max_length=20, 
        choices=OPCIONES_ALIADO, 
        default='GFR',
        verbose_name="Firma Consultora (Aliado)"
    )
    
    # Identidad Visual
    logo = models.ImageField(upload_to='logos_empresas/', blank=True, null=True)
    color_primario = models.CharField(max_length=7, default="#000000")
    email_soporte = models.EmailField()

    # CONFIGURACIÓN DE SERVICIOS CONTRATADOS
    tiene_sagrilaft = models.BooleanField(default=True, verbose_name="Activar Bloque SAGRILAFT")
    tiene_sarlaft = models.BooleanField(default=False)
    tiene_ptee = models.BooleanField(default=False, verbose_name="Activar Bloque PTEE")

    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Visibilidad restringida: solo el superusuario ve y gestiona esta empresa
    solo_superadmin = models.BooleanField(
        default=False,
        verbose_name="Solo para Superadmin",
        help_text="Si está activo, esta empresa solo la ve y gestiona el superusuario"
    )

    # Configuración personalizada de encuesta (opcional)
    config_encuesta = models.JSONField(
        null=True,
        blank=True,
        default=None,
        verbose_name="Configuración personalizada de encuesta",
        help_text="JSON con tipos de tercero, campos y preguntas adicionales"
    )

    objects = EmpresaClienteQuerySet.as_manager()

    def __str__(self):
        return self.nombre