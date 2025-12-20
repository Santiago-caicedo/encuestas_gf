from django.contrib import admin
from .models import RegistroEncuesta

@admin.register(RegistroEncuesta)
class RegistroEncuestaAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'nombre_respondiente', 'tipo_tercero', 'fecha_registro')
    list_filter = ('empresa', 'tipo_tercero', 'fecha_registro')
    search_fields = ('nombre_respondiente', 'empresa__nombre')
    readonly_fields = ('respuestas_data', 'ip_origen', 'fecha_registro')