from django.urls import path
from . import views

urlpatterns = [
    # Esta es la nueva URL única por empresa (ej: /encuesta/coca-cola/)
    path('encuesta/<slug:slug>/', views.ver_encuesta_publica, name='ver_encuesta'),
    path('encuesta/<slug:slug>/gracias/', views.encuesta_exito, name='encuesta_exito'),
]