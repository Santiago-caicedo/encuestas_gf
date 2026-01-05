"""
Script para crear y configurar la empresa Prodesa y CIA S.A. con encuesta personalizada.

=== INSTRUCCIONES DE USO ===

En el servidor de producción (AWS), ejecutar:

    cd /ruta/al/proyecto
    source venv/bin/activate  # o el entorno virtual que uses
    python manage.py shell < scripts/crear_prodesa.py

O desde el shell de Django:

    python manage.py shell
    >>> exec(open('scripts/crear_prodesa.py').read())

=== IMPORTANTE ===
- Este script es idempotente: si Prodesa ya existe, solo actualiza la configuración
- Revisa los valores de DATOS_EMPRESA antes de ejecutar en producción
"""

from empresas.models import EmpresaCliente

# ============================================================
# DATOS DE LA EMPRESA - MODIFICAR SEGÚN SEA NECESARIO
# ============================================================
DATOS_EMPRESA = {
    'nombre': 'Prodesa y CIA S.A.',
    'slug': 'prodesa',  # URL: /encuesta/prodesa/
    'aliado': 'GFR',  # Opciones: 'GFR' o 'LEGAL_SHIELD'
    'email_soporte': 'cumplimiento@prodesa.com',  # Cambiar por email real
    'color_primario': '#1e40af',  # Azul corporativo (cambiar si es necesario)
    'tiene_sagrilaft': True,
    'tiene_sarlaft': False,
    'tiene_ptee': True,
    'activo': True,
}

# ============================================================
# CONFIGURACIÓN PERSONALIZADA DE ENCUESTA PARA PRODESA
# ============================================================
CONFIG_ENCUESTA_PRODESA = {
    "tipos_tercero": [
        {"value": "CLIENTE", "label": "Cliente"},
        {"value": "PROVEEDOR", "label": "Proveedor"},
        {"value": "COLABORADOR", "label": "Colaborador"},
        {"value": "CONTRATISTA", "label": "Contratista"},
        {"value": "PROPIEDAD_HORIZONTAL", "label": "Propiedad Horizontal"},
        {"value": "OTRO", "label": "Otro"}
    ],
    "campos_seccion1": [
        {
            "name": "nit_cedula",
            "label": "NIT o Cédula de la Contraparte",
            "type": "text",
            "required": True,
            "placeholder": "Ingrese NIT o número de cédula"
        }
    ],
    "preguntas_seccion1": [
        {
            "name": "tiene_programa_laft",
            "texto": "¿Cuenta con programa de prevención de riesgos LA/FT/FPADM?",
            "tipo": "si_no"
        },
        {
            "name": "tiene_oficial_uiaf_laft",
            "texto": "¿Cuenta con oficial de cumplimiento registrado en UIAF para el programa de prevención de riesgos LA/FT/FPADM?",
            "tipo": "si_no"
        },
        {
            "name": "tiene_oficial_uiaf_ptee",
            "texto": "¿Cuenta con oficial de cumplimiento registrado en UIAF para el Programa de Transparencia y Ética Empresarial PTEE?",
            "tipo": "si_no"
        }
    ]
}

# ============================================================
# EJECUCIÓN DEL SCRIPT
# ============================================================
print("=" * 60)
print("SCRIPT: Crear/Configurar Prodesa y CIA S.A.")
print("=" * 60)

# Verificar si ya existe
empresa_existente = EmpresaCliente.objects.filter(slug=DATOS_EMPRESA['slug']).first()

if empresa_existente:
    print(f"\n[INFO] La empresa '{empresa_existente.nombre}' ya existe (ID: {empresa_existente.id})")
    print("[INFO] Actualizando configuración de encuesta...")

    empresa_existente.config_encuesta = CONFIG_ENCUESTA_PRODESA
    empresa_existente.save()

    empresa = empresa_existente
    accion = "ACTUALIZADA"
else:
    print(f"\n[INFO] Creando nueva empresa: {DATOS_EMPRESA['nombre']}")

    empresa = EmpresaCliente.objects.create(
        nombre=DATOS_EMPRESA['nombre'],
        slug=DATOS_EMPRESA['slug'],
        aliado=DATOS_EMPRESA['aliado'],
        email_soporte=DATOS_EMPRESA['email_soporte'],
        color_primario=DATOS_EMPRESA['color_primario'],
        tiene_sagrilaft=DATOS_EMPRESA['tiene_sagrilaft'],
        tiene_sarlaft=DATOS_EMPRESA['tiene_sarlaft'],
        tiene_ptee=DATOS_EMPRESA['tiene_ptee'],
        activo=DATOS_EMPRESA['activo'],
        config_encuesta=CONFIG_ENCUESTA_PRODESA
    )

    accion = "CREADA"

# Resumen
print("\n" + "=" * 60)
print(f"EMPRESA {accion} EXITOSAMENTE")
print("=" * 60)
print(f"""
Datos de la empresa:
  - ID: {empresa.id}
  - Nombre: {empresa.nombre}
  - Slug: {empresa.slug}
  - URL Encuesta: /encuesta/{empresa.slug}/
  - Aliado: {empresa.aliado}
  - Email: {empresa.email_soporte}
  - Color: {empresa.color_primario}

Servicios activos:
  - SAGRILAFT: {'Sí' if empresa.tiene_sagrilaft else 'No'}
  - SARLAFT: {'Sí' if empresa.tiene_sarlaft else 'No'}
  - PTEE: {'Sí' if empresa.tiene_ptee else 'No'}

Configuración personalizada de encuesta:
  - Tipos de tercero: {len(CONFIG_ENCUESTA_PRODESA['tipos_tercero'])} opciones
    {', '.join([t['label'] for t in CONFIG_ENCUESTA_PRODESA['tipos_tercero']])}

  - Campos adicionales: {len(CONFIG_ENCUESTA_PRODESA['campos_seccion1'])}
    * NIT o Cédula de la Contraparte

  - Preguntas adicionales: {len(CONFIG_ENCUESTA_PRODESA['preguntas_seccion1'])}
    * Programa LA/FT/FPADM
    * Oficial UIAF para LA/FT/FPADM
    * Oficial UIAF para PTEE
""")

print("=" * 60)
print("SCRIPT COMPLETADO")
print("=" * 60)
