from django.db import models
from empresas.models import EmpresaCliente

class RegistroEncuesta(models.Model):
    TIPO_TERCERO_CHOICES = [
        ('CLIENTE', 'Cliente'),
        ('PROVEEDOR', 'Proveedor'),
        ('EMPLEADO', 'Empleado'),
        ('OTRO', 'Otro'),
    ]

    empresa = models.ForeignKey(EmpresaCliente, on_delete=models.CASCADE, related_name='registros')
    
    # 1. Datos de Identificación (Según PDF [cite: 11-14])
    tipo_tercero = models.CharField(max_length=20, choices=TIPO_TERCERO_CHOICES)
    nombre_respondiente = models.CharField(max_length=255, verbose_name="Nombre / Razón Social")
    area = models.CharField(max_length=100, verbose_name="Área")
    cargo = models.CharField(max_length=100, verbose_name="Cargo")
    
    # 2. Las Respuestas se guardan en JSON para flexibilidad
    # Ejemplo: {"p5_sagrilaft": "SI", "p6_datos": "NO"}
    respuestas_data = models.JSONField(default=dict)
    
    # Metadatos
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre_respondiente} - {self.empresa.nombre}"