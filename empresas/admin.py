from django.contrib import admin
from .models import EmpresaCliente

@admin.register(EmpresaCliente)
class EmpresaClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug', 'color_primario', 'activo')
    search_fields = ('nombre',)