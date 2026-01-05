# Deployment: Encuesta Personalizada Prodesa

## Pasos para ejecutar en producción (AWS)

### 1. Conectarse al servidor
```bash
ssh usuario@tu-servidor-aws
cd /ruta/al/proyecto/gestion_riesgos
```

### 2. Activar entorno virtual
```bash
source venv/bin/activate
```

### 3. Aplicar la migración
```bash
python manage.py migrate empresas
```

Salida esperada:
```
Operations to perform:
  Apply all migrations: empresas
Running migrations:
  Applying empresas.0004_config_encuesta... OK
```

### 4. Crear y configurar Prodesa

**IMPORTANTE:** Antes de ejecutar, revisa el archivo `scripts/crear_prodesa.py` y ajusta:
- `email_soporte`: Email real de Prodesa
- `color_primario`: Color corporativo de Prodesa
- `aliado`: 'GFR' o 'LEGAL_SHIELD'
- Servicios: `tiene_sagrilaft`, `tiene_sarlaft`, `tiene_ptee`

Luego ejecutar:
```bash
python manage.py shell < scripts/crear_prodesa.py
```

### 5. Reiniciar el servidor (si aplica)
```bash
# Si usas gunicorn
sudo systemctl restart gunicorn

# Si usas supervisor
sudo supervisorctl restart gestion_riesgos
```

### 6. Verificar
Acceder a: `https://tu-dominio.com/encuesta/prodesa/`

---

## Rollback (si algo falla)

### Revertir migración
```bash
python manage.py migrate empresas 0003_empresacliente_tiene_sarlaft
```

### Eliminar empresa Prodesa (si es necesario)
```bash
python manage.py shell -c "from empresas.models import EmpresaCliente; EmpresaCliente.objects.filter(slug='prodesa').delete(); print('Eliminada')"
```

---

## Archivos modificados en este release

| Archivo | Descripción |
|---------|-------------|
| `empresas/models.py` | Campo `config_encuesta` agregado |
| `empresas/migrations/0004_config_encuesta.py` | Nueva migración |
| `formularios/views.py` | Soporte para config personalizada |
| `formularios/templates/formularios/encuesta_publica.html` | Template dinámico |
| `dashboard/views.py` | Métricas y exportación actualizadas |
| `dashboard/templates/dashboard/metricas.html` | Gráficos adicionales |
| `scripts/crear_prodesa.py` | Script de configuración |
