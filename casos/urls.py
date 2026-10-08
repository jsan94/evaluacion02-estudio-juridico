from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),

    # Mantenedor web de clientes
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/nuevo/', views.crear_cliente, name='crear_cliente'),
    path('clientes/<int:id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:id>/eliminar/', views.eliminar_cliente, name='eliminar_cliente'),

    # Casos
    path('casos/', views.lista_casos, name='lista_casos'),
    path('casos/<int:id>/', views.detalle_caso, name='detalle_caso'),
    path('casos/api/<int:id>/', views.api_caso, name='api_caso'),

    # Documento de un expediente
    path('expedientes/<int:id>/documento/', views.subir_documento, name='subir_documento'),
]
