from django.shortcuts import render, get_object_or_404, redirect
from empresas.models import EmpresaCliente
from .models import RegistroEncuesta
from core.security import sanitize_string, sanitize_dict, get_client_ip, rate_limit


@rate_limit(key_prefix='encuesta', max_requests=10, window_seconds=60)
def ver_encuesta_publica(request, slug):
    empresa = get_object_or_404(EmpresaCliente, slug=slug, activo=True)

    if request.method == 'POST':
        datos = request.POST

        # SEGURIDAD: Sanitizar todos los datos de entrada para prevenir XSS
        campos_excluidos = ['csrfmiddlewaretoken', 'nombre', 'area', 'cargo', 'tipo_tercero', 'nombre_contacto']
        respuestas_raw = {k: v for k, v in datos.items() if k not in campos_excluidos}
        respuestas_sanitizadas = sanitize_dict(respuestas_raw)

        # Guardamos la respuesta con datos sanitizados
        RegistroEncuesta.objects.create(
            empresa=empresa,
            tipo_tercero=sanitize_string(datos.get('tipo_tercero', '')),
            nombre_respondiente=sanitize_string(datos.get('nombre', '')),
            area=sanitize_string(datos.get('area', '')),
            cargo=sanitize_string(datos.get('cargo', '')),
            respuestas_data=respuestas_sanitizadas,
            ip_origen=get_client_ip(request)  # SEGURIDAD: Obtener IP real considerando proxies
        )

        return redirect('encuesta_exito', slug=slug)

    # Calcular números de sección dinámicamente
    seccion_num = 1  # Información General siempre es 1
    secciones = {'info_general': seccion_num}

    if empresa.tiene_sagrilaft:
        seccion_num += 1
        secciones['sagrilaft'] = seccion_num

    if empresa.tiene_sarlaft:
        seccion_num += 1
        secciones['sarlaft'] = seccion_num

    if empresa.tiene_ptee:
        seccion_num += 1
        secciones['ptee'] = seccion_num

    seccion_num += 1
    secciones['observaciones'] = seccion_num

    return render(request, 'formularios/encuesta_publica.html', {
        'empresa': empresa,
        'secciones': secciones,
    })


def encuesta_exito(request, slug):
    # SEGURIDAD: Solo mostrar página de gracias si la empresa está activa
    empresa = get_object_or_404(EmpresaCliente, slug=slug, activo=True)
    return render(request, 'formularios/gracias.html', {'empresa': empresa})