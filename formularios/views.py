from django.shortcuts import render, get_object_or_404, redirect
from empresas.models import EmpresaCliente
from .models import RegistroEncuesta

def ver_encuesta_publica(request, slug):
    empresa = get_object_or_404(EmpresaCliente, slug=slug, activo=True)
    
    if request.method == 'POST':
        datos = request.POST
        
        # Guardamos la respuesta
        RegistroEncuesta.objects.create(
            empresa=empresa,
            tipo_tercero=datos.get('tipo_tercero'),
            nombre_respondiente=datos.get('nombre'),
            area=datos.get('area'),
            cargo=datos.get('cargo'),
            # Filtramos para no guardar el csrf token ni los campos que ya sacamos aparte
            respuestas_data={k: v for k, v in datos.items() if k not in ['csrfmiddlewaretoken', 'nombre', 'area', 'cargo', 'tipo_tercero', 'nombre_contacto']},
            ip_origen=request.META.get('REMOTE_ADDR')
        )
        
        # AQUÍ ESTÁ EL CAMBIO CLAVE:
        # En lugar de render(...), usamos redirect a la nueva URL de éxito
        return redirect('encuesta_exito', slug=slug)

    return render(request, 'formularios/encuesta_publica.html', {
        'empresa': empresa
    })


def encuesta_exito(request, slug):
    # Solo buscamos la empresa para pintar el logo y colores en la página de gracias
    empresa = get_object_or_404(EmpresaCliente, slug=slug)
    return render(request, 'formularios/gracias.html', {'empresa': empresa})