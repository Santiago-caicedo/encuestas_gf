import datetime
from django.db.models.functions import ExtractYear
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from .forms import EmpresaForm, NuevoUsuarioForm
from empresas.models import EmpresaCliente
from django.contrib.auth.models import User
from django.db.models import Count, Q
from formularios.models import RegistroEncuesta
from django.core.paginator import Paginator
import csv
from django.http import HttpResponse



@login_required
def dashboard_home(request):
    # Métricas Globales
    total_empresas = EmpresaCliente.objects.filter(activo=True).count()
    total_registros = RegistroEncuesta.objects.count()
    
    # Actividad Reciente (Últimos 10 registros de CUALQUIER empresa)
    ultimos_registros = RegistroEncuesta.objects.all().order_by('-fecha_registro')[:10]
    
    return render(request, 'dashboard/global_home.html', {
        'total_empresas': total_empresas,
        'total_registros': total_registros,
        'ultimos_registros': ultimos_registros
    })

# 2. SECCIÓN EMPRESAS Y CLIENTES 
@login_required
def lista_empresas(request):
    # 1. Obtener parámetros de la URL
    query = request.GET.get('q', '')
    filtro_aliado = request.GET.get('aliado', '')

    # 2. Query Base
    empresas = EmpresaCliente.objects.all().order_by('-created_at')

    # 3. Aplicar Filtros
    if query:
        # Busca por nombre O por slug (insensible a mayúsculas)
        empresas = empresas.filter(Q(nombre__icontains=query) | Q(slug__icontains=query))
    
    if filtro_aliado:
        empresas = empresas.filter(aliado=filtro_aliado)

    return render(request, 'dashboard/lista_empresas.html', {
        'empresas': empresas,
        'query': query,
        'filtro_aliado': filtro_aliado
    })

@login_required
def crear_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_empresas')
    else:
        form = EmpresaForm()
    return render(request, 'dashboard/crear_empresa.html', {'form': form})


@login_required
def editar_empresa(request, id):
    # Buscamos la empresa, si no existe devuelve error 404
    empresa = get_object_or_404(EmpresaCliente, id=id)
    
    if request.method == 'POST':
        # 'instance=empresa' es la CLAVE: le dice a Django que actualice este registro, no que cree uno nuevo
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            return redirect('lista_empresas')
    else:
        # Pre-llenamos el formulario con los datos actuales
        form = EmpresaForm(instance=empresa)

    # Reutilizamos la plantilla de crear, pero le pasamos la variable 'editar': True
    return render(request, 'dashboard/crear_empresa.html', {
        'form': form, 
        'empresa': empresa,
        'editar': True 
    })



# Asegúrate de importar RegistroEncuesta arriba

@login_required
def ver_metricas(request, id):
    empresa = get_object_or_404(EmpresaCliente, id=id)
    
    # 1. GESTIÓN DE AÑOS (VIGENCIAS)
    # Obtenemos los años disponibles en la BD para esta empresa
    anios_disponibles = empresa.registros.annotate(anio=ExtractYear('fecha_registro')).values_list('anio', flat=True).distinct().order_by('-anio')
    
    # Año actual por defecto
    anio_actual = datetime.date.today().year
    
    # Si el usuario seleccionó un año en el dropdown, lo usamos. Si no, usamos el actual.
    anio_seleccionado = int(request.GET.get('vigencia', anio_actual))
    
    # Si no hay registros aún, forzamos que aparezca el año actual en la lista
    lista_anios = list(anios_disponibles)
    if anio_actual not in lista_anios:
        lista_anios.insert(0, anio_actual)

    # 2. FILTRADO BASE (Toda la data de la vista dependerá de esto)
    # Filtramos los registros GLOBALES de la vista por el año seleccionado
    registros_anio = empresa.registros.filter(fecha_registro__year=anio_seleccionado).order_by('-fecha_registro')
    total = registros_anio.count()

    # 3. FILTROS ADICIONALES (Tabla)
    # Estos filtros operan SOBRE el conjunto del año seleccionado
    f_tipo = request.GET.get('tipo')
    registros_tabla = registros_anio # Copia para filtrar

    if f_tipo:
        registros_tabla = registros_tabla.filter(tipo_tercero=f_tipo)

    registros_visuales = registros_tabla[:50]

    # 4. GRÁFICOS (Ahora usan 'registros_anio' en lugar de todos)
    
    # A) Demografía
    data_distribucion = registros_anio.values('tipo_tercero').annotate(total=Count('id')).order_by()
    labels_tipos = [item['tipo_tercero'] for item in data_distribucion]
    data_tipos = [item['total'] for item in data_distribucion]

    # B) SAGRILAFT
    stats_sagrilaft = {}
    if empresa.tiene_sagrilaft: # Quitamos la condición 'and total > 0' para que pinte vacíos si es año nuevo
        conocen = registros_anio.filter(respuestas_data__p5_sagrilaft_conoce='SI').count()
        no_conocen = total - conocen
        stats_sagrilaft['conocimiento'] = [conocen, no_conocen]
        
        saben_denunciar = registros_anio.filter(respuestas_data__p8_sagrilaft_denuncia='SI').count()
        no_saben = total - saben_denunciar
        stats_sagrilaft['denuncia'] = [saben_denunciar, no_saben]

    # C) PTEE
    stats_ptee = {}
    if empresa.tiene_ptee:
        conocen_ptee = registros_anio.filter(respuestas_data__p9_ptee_conoce='SI').count()
        no_conocen_ptee = total - conocen_ptee
        stats_ptee['conocimiento'] = [conocen_ptee, no_conocen_ptee]

    return render(request, 'dashboard/metricas.html', {
        'empresa': empresa,
        'total': total,
        'registros': registros_visuales,
        # Variables nuevas para el control de años
        'lista_anios': lista_anios,
        'anio_seleccionado': anio_seleccionado,
        # Resto de contexto
        'filtros': {'tipo': f_tipo},
        'labels_tipos': labels_tipos,
        'data_tipos': data_tipos,
        'stats_sagrilaft': stats_sagrilaft,
        'stats_ptee': stats_ptee,
    })

@login_required
def ver_detalle_respuesta(request, id):
    registro = get_object_or_404(RegistroEncuesta, id=id)
    return render(request, 'dashboard/detalle_respuesta.html', {
        'registro': registro,
        'empresa': registro.empresa
    })



@login_required
def ver_todos_registros(request, id):
    empresa = get_object_or_404(EmpresaCliente, id=id)
    registros = empresa.registros.all().order_by('-fecha_registro')

    # Filtros
    f_tipo = request.GET.get('tipo')
    f_inicio = request.GET.get('fecha_inicio')
    f_fin = request.GET.get('fecha_fin')
    f_nombre = request.GET.get('nombre') # Filtro extra por nombre

    if f_tipo:
        registros = registros.filter(tipo_tercero=f_tipo)
    if f_inicio:
        registros = registros.filter(fecha_registro__date__gte=f_inicio)
    if f_fin:
        registros = registros.filter(fecha_registro__date__lte=f_fin)
    if f_nombre:
        registros = registros.filter(nombre_respondiente__icontains=f_nombre)

    # Paginación: Mostrar 50 por página
    paginator = Paginator(registros, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dashboard/todos_registros.html', {
        'empresa': empresa,
        'page_obj': page_obj,
        'filtros': {'tipo': f_tipo, 'inicio': f_inicio, 'fin': f_fin, 'nombre': f_nombre}
    })



@login_required
def exportar_excel(request, id):
    empresa = get_object_or_404(EmpresaCliente, id=id)
    registros = empresa.registros.all().order_by('-fecha_registro')

    # 1. APLICAMOS LOS MISMOS FILTROS (Para exportar lo que se ve)
    f_tipo = request.GET.get('tipo')
    f_inicio = request.GET.get('fecha_inicio')
    f_fin = request.GET.get('fecha_fin')
    f_nombre = request.GET.get('nombre')

    if f_tipo:
        registros = registros.filter(tipo_tercero=f_tipo)
    if f_inicio:
        registros = registros.filter(fecha_registro__date__gte=f_inicio)
    if f_fin:
        registros = registros.filter(fecha_registro__date__lte=f_fin)
    if f_nombre:
        registros = registros.filter(nombre_respondiente__icontains=f_nombre)

    # 2. PREPARAMOS EL ARCHIVO HTTP (Tipo CSV compatible con Excel)
    response = HttpResponse(content_type='text/csv')
    nombre_archivo = f"Reporte_{empresa.slug}_{request.GET.get('fecha_inicio', 'inicio')}_a_{request.GET.get('fecha_fin', 'fin')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'

    # IMPORTANTE: Esto agrega el BOM para que Excel reconozca tildes y ñ
    response.write(u'\ufeff'.encode('utf8'))

    # Usamos punto y coma (;) que es el estándar de Excel en español
    writer = csv.writer(response, delimiter=';')

    # 3. ESCRIBIMOS EL ENCABEZADO
    headers = [
        'ID', 'Fecha Registro', 'Tipo Tercero', 'Nombre / Razón Social', 
        'Área', 'Cargo', 'IP Origen'
    ]
    
    # Agregamos columnas dinámicas según lo contratado
    if empresa.tiene_sagrilaft:
        headers.extend([
            'SAGRILAFT - ¿Conoce Sistema?', 
            'SAGRILAFT - ¿Datos Actualizados?', 
            'SAGRILAFT - ¿Fue Informado?', 
            'SAGRILAFT - ¿Conoce Canales Denuncia?'
        ])
    
    if empresa.tiene_ptee:
        headers.extend([
            'PTEE - ¿Conoce Programa?', 
            'PTEE - ¿Conoce Código Ética?', 
            'PTEE - ¿Sabe Conflicto Interés?', 
            'PTEE - ¿Conoce Canales Soborno?'
        ])
    
    headers.append('Observaciones')
    writer.writerow(headers)

    # 4. ESCRIBIMOS LAS FILAS
    for reg in registros:
        data = reg.respuestas_data # El JSON
        
        row = [
            reg.id,
            reg.fecha_registro.strftime("%d/%m/%Y %H:%M"),
            reg.tipo_tercero,
            reg.nombre_respondiente,
            reg.area,
            reg.cargo,
            reg.ip_origen
        ]

        if empresa.tiene_sagrilaft:
            row.extend([
                data.get('p5_sagrilaft_conoce', '-'),
                data.get('p6_sagrilaft_actualizado', '-'),
                data.get('p7_sagrilaft_informado', '-'),
                data.get('p8_sagrilaft_denuncia', '-')
            ])

        if empresa.tiene_ptee:
            row.extend([
                data.get('p9_ptee_conoce', '-'),
                data.get('p10_ptee_codigo', '-'),
                data.get('p11_ptee_conflicto', '-'),
                data.get('p12_ptee_corrupcion', '-')
            ])
            
        row.append(data.get('observaciones', ''))
        
        writer.writerow(row)

    return response



# Función de seguridad: ¿Es superusuario?
def es_superusuario(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(es_superusuario, login_url='dashboard_home')
def usuarios_internos(request):
    usuarios = User.objects.all().order_by('-date_joined')
    
    if request.method == 'POST':
        form = NuevoUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('usuarios_internos')
    else:
        form = NuevoUsuarioForm()

    return render(request, 'dashboard/usuarios.html', {
        'usuarios': usuarios,
        'form': form
    })

@user_passes_test(es_superusuario, login_url='dashboard_home')
def eliminar_usuario(request, id):
    user_to_delete = get_object_or_404(User, id=id)
    # Evitar que te borres a ti mismo
    if user_to_delete.id != request.user.id:
        user_to_delete.delete()
    return redirect('usuarios_internos')

@login_required
def configuracion_global(request):
    # Aquí iría la configuración general del sistema
    return render(request, 'dashboard/seccion_en_construccion.html', {
        'titulo': 'Configuración Global',
        'descripcion': 'Parámetros generales del sistema, correos de notificación y seguridad.'
    })