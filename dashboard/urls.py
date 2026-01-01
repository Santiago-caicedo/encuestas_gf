from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('metricas-globales/', views.metricas_globales, name='metricas_globales'),
    path('empresas/', views.lista_empresas, name='lista_empresas'),
    path('nueva-empresa/', views.crear_empresa, name='crear_empresa'),
    path('empresa/<int:id>/editar/', views.editar_empresa, name='editar_empresa'),
    path('empresa/<int:id>/registros/', views.ver_todos_registros, name='ver_todos_registros'),
    path('empresa/<int:id>/metricas/', views.ver_metricas, name='ver_metricas'),
    path('empresa/<int:id>/exportar/', views.exportar_excel, name='exportar_excel'),    
    path('respuesta/<int:id>/detalle/', views.ver_detalle_respuesta, name='ver_detalle_respuesta'),
    path('usuarios/', views.usuarios_internos, name='usuarios_internos'),
    path('usuarios/<int:id>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('configuracion/', views.configuracion_global, name='configuracion_global'),
]