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
    # Extraemos los años disponibles en los registros para llenar el selector
    anios_disponibles = empresa.registros.annotate(anio=ExtractYear('fecha_registro')).values_list('anio', flat=True).distinct().order_by('-anio')
    
    anio_actual = datetime.date.today().year
    
    # Intentamos obtener el año de la URL, si no, usamos el actual
    try:
        anio_seleccionado = int(request.GET.get('vigencia', anio_actual))
    except ValueError:
        anio_seleccionado = anio_actual
    
    # Aseguramos que el año actual aparezca en la lista aunque no haya registros aún
    lista_anios = list(anios_disponibles)
    if anio_actual not in lista_anios:
        lista_anios.insert(0, anio_actual)

    # 2. QUERYSET BASE (Filtrado por Año)
    # Todos los cálculos estadísticos se basan en este conjunto del año seleccionado
    registros_anio = empresa.registros.filter(fecha_registro__year=anio_seleccionado).order_by('-fecha_registro')
    total = registros_anio.count()

    # 3. FILTROS ADICIONALES (Solo para la Tabla Visual)
    # Estos filtros permiten buscar en la tabla sin afectar los gráficos globales del año
    f_tipo = request.GET.get('tipo')
    f_inicio = request.GET.get('fecha_inicio')
    f_fin = request.GET.get('fecha_fin')

    registros_tabla = registros_anio 

    if f_tipo:
        registros_tabla = registros_tabla.filter(tipo_tercero=f_tipo)
    if f_inicio:
        registros_tabla = registros_tabla.filter(fecha_registro__date__gte=f_inicio)
    if f_fin:
        registros_tabla = registros_tabla.filter(fecha_registro__date__lte=f_fin)

    # Limitamos a 50 para no saturar el DOM, el resto se ve en "Ver Todos"
    registros_visuales = registros_tabla[:50]

    # 4. CÁLCULO DE GRÁFICOS Y KPIs

    # A) Demografía (Distribución por Tipo de Tercero)
    # NOTA: .order_by() vacío al final es CRÍTICO para limpiar el ordenamiento por fecha 
    # y permitir que el annotate agrupe correctamente.
    data_distribucion = registros_anio.values('tipo_tercero').annotate(total=Count('id')).order_by()
    
    labels_tipos = [item['tipo_tercero'] for item in data_distribucion]
    data_tipos = [item['total'] for item in data_distribucion]

    # B) SAGRILAFT (Si aplica)
    stats_sagrilaft = {}
    if empresa.tiene_sagrilaft:
        # Pregunta 5: Conocimiento del Sistema
        conocen = registros_anio.filter(respuestas_data__p5_sagrilaft_conoce='SI').count()
        no_conocen = total - conocen
        stats_sagrilaft['conocimiento'] = [conocen, no_conocen]
        
        # Pregunta 8: Canales de Denuncia
        saben_denunciar = registros_anio.filter(respuestas_data__p8_sagrilaft_denuncia='SI').count()
        no_saben = total - saben_denunciar
        stats_sagrilaft['denuncia'] = [saben_denunciar, no_saben]

    # C) SARLAFT (NUEVO - Si aplica)
    stats_sarlaft = {}
    if empresa.tiene_sarlaft:
        # Pregunta 5: Conocimiento del Sistema SARLAFT
        conocen_sar = registros_anio.filter(respuestas_data__p5_sarlaft_conoce='SI').count()
        no_conocen_sar = total - conocen_sar
        stats_sarlaft['conocimiento'] = [conocen_sar, no_conocen_sar]
        
        # Pregunta 8: Canales de Denuncia SARLAFT
        saben_denunciar_sar = registros_anio.filter(respuestas_data__p8_sarlaft_denuncia='SI').count()
        no_saben_sar = total - saben_denunciar_sar
        stats_sarlaft['denuncia'] = [saben_denunciar_sar, no_saben_sar]

    # D) PTEE (Si aplica)
    stats_ptee = {}
    if empresa.tiene_ptee:
        # Pregunta 9: Conocimiento del PTEE
        conocen_ptee = registros_anio.filter(respuestas_data__p9_ptee_conoce='SI').count()
        no_conocen_ptee = total - conocen_ptee
        stats_ptee['conocimiento'] = [conocen_ptee, no_conocen_ptee]

    # 5. RENDERIZADO
    return render(request, 'dashboard/metricas.html', {
        'empresa': empresa,
        'total': total,
        'registros': registros_visuales,
        # Variables de contexto para filtros y años
        'lista_anios': lista_anios,
        'anio_seleccionado': anio_seleccionado,
        'filtros': {'tipo': f_tipo, 'inicio': f_inicio, 'fin': f_fin},
        # Datos para Chart.js
        'labels_tipos': labels_tipos,
        'data_tipos': data_tipos,
        'stats_sagrilaft': stats_sagrilaft,
        'stats_sarlaft': stats_sarlaft, # Nuevo
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
    # SEGURIDAD: Límite máximo de registros para evitar memory exhaustion
    MAX_EXPORT_RECORDS = 10000

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

    # SEGURIDAD: Aplicar límite máximo
    total_registros = registros.count()
    registros = registros[:MAX_EXPORT_RECORDS]

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
    # SEGURIDAD: Solo permitir eliminación vía POST
    if request.method != 'POST':
        return redirect('usuarios_internos')

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