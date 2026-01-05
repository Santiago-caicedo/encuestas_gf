# Sistema de Gestión de Riesgos SAGRILAFT/PTEE

## Descripción General

Sistema web para gestionar encuestas de cumplimiento normativo (SAGRILAFT, SARLAFT, PTEE) para empresas clientes. Desarrollado en Django con PostgreSQL.

## Stack Tecnológico

- **Backend:** Django 5.2.9
- **Base de datos:** PostgreSQL
- **Frontend:** Tailwind CSS (CDN), Chart.js, Font Awesome
- **Almacenamiento:** AWS S3 (producción), Local (desarrollo)
- **Servidor:** WSGI/ASGI

## Estructura del Proyecto

```
gestion_riesgos/
├── core/                    # Configuración central Django
│   ├── settings.py          # Configuración principal
│   ├── urls.py              # Rutas globales
│   ├── backends.py          # EmailBackend (login con email)
│   ├── auth_views.py        # Login seguro con rate limiting
│   └── security.py          # Sanitización XSS, rate limiting
├── empresas/                # App de empresas clientes
│   ├── models.py            # EmpresaCliente
│   └── migrations/
├── formularios/             # App de encuestas públicas
│   ├── models.py            # RegistroEncuesta
│   ├── views.py             # ver_encuesta_publica
│   └── templates/formularios/
├── dashboard/               # App de administración
│   ├── views.py             # Métricas, exportación, CRUD
│   ├── forms.py             # Formularios
│   └── templates/dashboard/
├── scripts/                 # Scripts de mantenimiento
│   ├── crear_prodesa.py     # Crear empresa con config personalizada
│   └── README_DEPLOY_PRODESA.md
├── static/                  # Archivos estáticos
├── media/                   # Logos de empresas
└── manage.py
```

## Modelos Principales

### EmpresaCliente (`empresas/models.py`)
```python
- nombre, slug (URL única)
- aliado: 'GFR' | 'LEGAL_SHIELD'
- logo, color_primario, email_soporte
- tiene_sagrilaft, tiene_sarlaft, tiene_ptee  # Módulos activos
- config_encuesta (JSONField)  # Configuración personalizada de encuesta
- activo, created_at
```

### RegistroEncuesta (`formularios/models.py`)
```python
- empresa (FK -> EmpresaCliente)
- tipo_tercero: CLIENTE | PROVEEDOR | EMPLEADO | OTRO | (personalizados)
- nombre_respondiente, area, cargo
- respuestas_data (JSONField)  # Todas las respuestas dinámicas
- fecha_registro, ip_origen
```

## Encuestas Personalizadas

El campo `config_encuesta` en `EmpresaCliente` permite personalizar encuestas por empresa:

```json
{
  "tipos_tercero": [
    {"value": "CLIENTE", "label": "Cliente"},
    {"value": "COLABORADOR", "label": "Colaborador"}
  ],
  "campos_seccion1": [
    {"name": "nit_cedula", "label": "NIT o Cédula", "type": "text", "required": true}
  ],
  "preguntas_seccion1": [
    {"name": "tiene_programa_laft", "texto": "¿Cuenta con programa LA/FT?", "tipo": "si_no"}
  ]
}
```

- Empresas sin `config_encuesta` → Usan valores por defecto
- Las respuestas personalizadas van al `respuestas_data` (JSONField)

## URLs Principales

| Ruta | Vista | Descripción |
|------|-------|-------------|
| `/encuesta/<slug>/` | `ver_encuesta_publica` | Encuesta pública (sin auth) |
| `/` | `dashboard_home` | Inicio del dashboard |
| `/metricas-globales/` | `metricas_globales` | Dashboard global |
| `/empresas/` | `lista_empresas` | CRUD empresas |
| `/empresa/<id>/metricas/` | `ver_metricas` | Métricas por empresa |
| `/empresa/<id>/exportar/` | `exportar_excel` | Exportar CSV |
| `/usuarios/` | `usuarios_internos` | Gestión usuarios (superuser) |

## Seguridad Implementada

- **Rate Limiting:** Login (5 intentos/5 min), Encuestas (10/min por IP)
- **Sanitización XSS:** `sanitize_string()`, `sanitize_dict()` en `core/security.py`
- **CSRF:** Middleware activo
- **Sesiones:** Expiran en 30 min
- **Producción:** HTTPS forzado, HSTS, cookies seguras

## Comandos Útiles

```bash
# Entorno virtual (Windows)
./venv/Scripts/python.exe manage.py <comando>

# Entorno virtual (Linux/Mac)
source venv/bin/activate && python manage.py <comando>

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Crear empresa con config personalizada
python manage.py shell -c "exec(open('scripts/crear_prodesa.py').read())"

# Ver config de una empresa
python manage.py shell -c "
from empresas.models import EmpresaCliente
import json
e = EmpresaCliente.objects.get(slug='prodesa')
print(json.dumps(e.config_encuesta, indent=2, ensure_ascii=False))
"
```

## Variables de Entorno (.env)

```
DEBUG=True
SECRET_KEY=...
ALLOWED_HOSTS=127.0.0.1,localhost
DB_NAME=sagrilaft_db
DB_USER=postgres
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432

# Producción (AWS S3)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=vadomdata
```

## Notas de Desarrollo

1. **JSONField es clave:** `respuestas_data` almacena respuestas dinámicas sin necesidad de migraciones
2. **Templates dinámicos:** Usan `{% if config %}` para renderizar campos personalizados
3. **Compatibilidad:** Empresas sin `config_encuesta` funcionan con valores por defecto
4. **Gráficos:** Chart.js renderiza datos pasados desde Django como `{{ data|safe }}`

## Deployment (AWS)

```bash
git pull origin main
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```
