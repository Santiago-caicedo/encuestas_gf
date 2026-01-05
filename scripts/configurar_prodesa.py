"""
Script para configurar la encuesta personalizada de Prodesa y CIA S.A.

Uso:
    python manage.py shell < scripts/configurar_prodesa.py

O ejecutar desde el shell de Django:
    exec(open('scripts/configurar_prodesa.py').read())
"""

from empresas.models import EmpresaCliente

# Configuración personalizada para Prodesa
CONFIG_PRODESA = {
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

# Buscar Prodesa por nombre (parcial) o slug
try:
    empresa = EmpresaCliente.objects.get(slug='prodesa')
    print(f"Empresa encontrada: {empresa.nombre} (ID: {empresa.id})")
except EmpresaCliente.DoesNotExist:
    # Buscar por nombre
    empresas = EmpresaCliente.objects.filter(nombre__icontains='prodesa')
    if empresas.exists():
        empresa = empresas.first()
        print(f"Empresa encontrada por nombre: {empresa.nombre} (ID: {empresa.id})")
    else:
        print("ERROR: No se encontró la empresa Prodesa.")
        print("Empresas disponibles:")
        for e in EmpresaCliente.objects.all():
            print(f"  - {e.nombre} (slug: {e.slug})")
        empresa = None

if empresa:
    # Aplicar configuración
    empresa.config_encuesta = CONFIG_PRODESA
    empresa.save()
    print(f"\n✓ Configuración aplicada exitosamente a '{empresa.nombre}'")
    print(f"\nTipos de tercero configurados:")
    for t in CONFIG_PRODESA['tipos_tercero']:
        print(f"  - {t['label']} ({t['value']})")
    print(f"\nCampos adicionales:")
    for c in CONFIG_PRODESA['campos_seccion1']:
        print(f"  - {c['label']}")
    print(f"\nPreguntas adicionales:")
    for p in CONFIG_PRODESA['preguntas_seccion1']:
        print(f"  - {p['texto'][:60]}...")
