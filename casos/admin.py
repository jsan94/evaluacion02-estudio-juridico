from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.template.defaultfilters import floatformat

from .models import Cliente, EstadoCaso, Caso, Expediente, Pago, PerfilAbogado


# ---------- Usuarios: PerfilAbogado como StackedInline ----------

class PerfilAbogadoInline(admin.StackedInline):
    model = PerfilAbogado
    can_delete = False
    verbose_name_plural = 'Perfil de abogado'


class UsuarioAdmin(UserAdmin):
    inlines = [PerfilAbogadoInline]
    list_display = ('username', 'first_name', 'last_name', 'email', 'colegiatura', 'is_staff')

    @admin.display(description='N.° colegiatura')
    def colegiatura(self, obj):
        if hasattr(obj, 'perfilabogado'):
            return obj.perfilabogado.numero_colegiatura
        return '-'


admin.site.unregister(User)
admin.site.register(User, UsuarioAdmin)


# ---------- Clientes ----------

class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'documento', 'telefono', 'correo')
    search_fields = ('nombres', 'documento', 'correo')
    list_filter = ('caso__estado',)


# ---------- Estados de caso ----------

class EstadoCasoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'permite_pagos')
    search_fields = ('nombre',)
    list_filter = ('permite_pagos',)


# ---------- Casos: Expediente y Pago como TabularInline ----------

class ExpedienteInline(admin.TabularInline):
    model = Expediente
    extra = 1


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 1


class CasoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'titulo', 'cliente', 'estado', 'total', 'fecha_inicio')
    search_fields = ('codigo', 'titulo', 'cliente__nombres', 'cliente__documento')
    list_filter = ('estado', 'abogados', 'fecha_inicio')
    filter_horizontal = ('abogados',)
    inlines = [ExpedienteInline, PagoInline]

    @admin.display(description='Total pagado')
    def total(self, obj):
        return f'S/ {floatformat(obj.total_pagado(), 2)}'


# ---------- Expedientes ----------

class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ('numero', 'juzgado', 'fecha_presentacion', 'caso')
    search_fields = ('numero', 'juzgado', 'caso__codigo')
    list_filter = ('juzgado', 'fecha_presentacion')


admin.site.register(Cliente, ClienteAdmin)
admin.site.register(EstadoCaso, EstadoCasoAdmin)
admin.site.register(Caso, CasoAdmin)
admin.site.register(Expediente, ExpedienteAdmin)
