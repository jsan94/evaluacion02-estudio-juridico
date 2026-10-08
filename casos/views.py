from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.template.defaultfilters import floatformat

from .models import Cliente, EstadoCaso, Caso, Expediente, Pago


def inicio(request):
    return redirect('lista_casos')


# =====================================================
# Mantenedor web de clientes
# =====================================================

def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'casos/clientes.html', {'clientes': clientes})


def formulario_cliente(request, cliente, titulo, mensaje):
    errores = []
    if request.method == 'POST':
        cliente.nombres = request.POST['nombres']
        cliente.documento = request.POST['documento']
        cliente.telefono = request.POST['telefono']
        cliente.correo = request.POST['correo']
        try:
            cliente.full_clean()   # valida en el modelo: DNI/RUC, documento único y correo
            cliente.save()
            messages.success(request, f'Cliente "{cliente.nombres}" {mensaje} correctamente.')
            return redirect('lista_clientes')
        except ValidationError as e:
            errores = e.messages
    return render(request, 'casos/cliente_form.html', {
        'titulo': titulo,
        'cliente': cliente,
        'errores': errores,
    })


def crear_cliente(request):
    return formulario_cliente(request, Cliente(), 'Nuevo cliente', 'registrado')


def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    return formulario_cliente(request, cliente, 'Editar cliente', 'actualizado')


def eliminar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    if request.method == 'POST':
        try:
            cliente.delete()
            messages.success(request, f'Cliente "{cliente.nombres}" eliminado.')
        except ProtectedError:
            # Caso.cliente tiene on_delete=PROTECT
            messages.error(request, f'No se puede eliminar a "{cliente.nombres}" porque tiene casos registrados.')
        return redirect('lista_clientes')
    return render(request, 'casos/cliente_eliminar.html', {'cliente': cliente})


# =====================================================
# Casos
# =====================================================

def lista_casos(request):
    # Filtro por estado: primero el de la URL (?estado=2); si no viene, el guardado en la cookie
    if 'estado' in request.GET:
        estado_id = request.GET['estado']
    else:
        estado_id = request.COOKIES.get('ultimo_estado', '')

    casos = Caso.objects.select_related('cliente', 'estado').prefetch_related('abogados')
    if estado_id.isdigit():
        casos = casos.filter(estado_id=estado_id)

    response = render(request, 'casos/lista_casos.html', {
        'casos': casos,
        'estados': EstadoCaso.objects.all(),
        'estado_actual': estado_id,
        'desde_cookie': 'estado' not in request.GET and estado_id != '',
    })

    # Guardar el último estado consultado para la siguiente visita (30 días)
    if 'estado' in request.GET:
        response.set_cookie('ultimo_estado', estado_id, max_age=60 * 60 * 24 * 30)
    return response


def detalle_caso(request, id):
    caso = get_object_or_404(Caso, id=id)

    # Registrar un pago enviado por POST
    if request.method == 'POST':
        pago = Pago(
            caso=caso,
            monto=request.POST.get('monto'),
            fecha=request.POST.get('fecha') or date.today(),
            descripcion=request.POST.get('descripcion'),
        )
        try:
            pago.full_clean()   # ejecuta Pago.clean(): solo se guarda si el estado del caso permite pagos
            pago.save()
            messages.success(request, f'Pago de S/ {floatformat(pago.monto, 2)} registrado correctamente.')
        except ValidationError as e:
            messages.error(request, 'Pago rechazado. ' + ' '.join(e.messages))
        return redirect('detalle_caso', id=caso.id)

    return render(request, 'casos/detalle_caso.html', {
        'caso': caso,
        'expedientes': caso.expediente_set.all(),
        'pagos': caso.pago_set.all(),
        'hoy': date.today(),
    })


def subir_documento(request, id):
    expediente = get_object_or_404(Expediente, id=id)
    if request.method == 'POST':
        if 'documento' in request.FILES:
            expediente.documento = request.FILES['documento']
            expediente.save()
            messages.success(request, f'Documento subido al expediente {expediente.numero}.')
        else:
            messages.error(request, 'Seleccione un archivo antes de subirlo.')
    return redirect('detalle_caso', id=expediente.caso_id)


def api_caso(request, id):
    try:
        caso = Caso.objects.get(id=id)
    except Caso.DoesNotExist:
        return JsonResponse({'error': 'Caso no encontrado'}, status=404)

    datos = {
        'codigo': caso.codigo,
        'cliente': caso.cliente.nombres,
        'estado': caso.estado.nombre,
        'abogados': [abogado.get_full_name() or abogado.username for abogado in caso.abogados.all()],
        'numero_expedientes': caso.expediente_set.count(),
        'total_pagado': float(caso.total_pagado()),
    }
    return JsonResponse(datos, json_dumps_params={'ensure_ascii': False, 'indent': 2})
