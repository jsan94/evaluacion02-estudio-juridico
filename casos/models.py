from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator


class Cliente(models.Model):
    nombres = models.CharField(max_length=150)
    documento = models.CharField(
        max_length=11,
        unique=True,
        validators=[RegexValidator(r'^(\d{8}|\d{11})$', 'El documento debe ser un DNI (8 dígitos) o un RUC (11 dígitos).')],
    )
    telefono = models.CharField('teléfono', max_length=15)
    correo = models.EmailField()

    class Meta:
        ordering = ['nombres']

    def __str__(self):
        return self.nombres


class EstadoCaso(models.Model):
    nombre = models.CharField(max_length=30, unique=True)
    permite_pagos = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'estado de caso'
        verbose_name_plural = 'estados de caso'

    def __str__(self):
        return self.nombre


class Caso(models.Model):
    codigo = models.CharField('código', max_length=20, unique=True)
    titulo = models.CharField('título', max_length=200)
    descripcion = models.TextField('descripción')
    fecha_inicio = models.DateField('fecha de inicio')
    # Uno a muchos: un cliente tiene muchos casos.
    # PROTECT: no se puede eliminar un cliente que tiene casos registrados.
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    # Uno a muchos: un estado agrupa muchos casos.
    # PROTECT: no se puede eliminar un estado que está siendo usado por algún caso.
    estado = models.ForeignKey(EstadoCaso, on_delete=models.PROTECT)
    # Muchos a muchos: un caso tiene varios abogados y un abogado revisa muchos casos.
    abogados = models.ManyToManyField(User, related_name='casos_asignados',
                                      limit_choices_to={'groups__name': 'Abogados'})

    class Meta:
        ordering = ['codigo']

    def __str__(self):
        return self.codigo

    def total_pagado(self):
        total = self.pago_set.aggregate(total=Sum('monto'))['total'] or 0
        return round(Decimal(total), 2)


class Expediente(models.Model):
    numero = models.CharField('número', max_length=30, unique=True)
    juzgado = models.CharField(max_length=150)
    fecha_presentacion = models.DateField('fecha de presentación')
    # Uno a muchos: un caso tiene varios expedientes.
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE)
    documento = models.FileField(upload_to='expedientes/', blank=True)

    class Meta:
        ordering = ['fecha_presentacion']

    def __str__(self):
        return self.numero


class Pago(models.Model):
    # Uno a muchos: un caso tiene muchos pagos.
    # CASCADE: un pago no tiene sentido sin su caso; si se elimina el caso, se eliminan sus pagos.
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    fecha = models.DateField()
    descripcion = models.CharField('descripción', max_length=200)

    class Meta:
        ordering = ['fecha', 'id']

    def __str__(self):
        return f'{self.caso} - S/ {self.monto}'

    def clean(self):
        # Regla de negocio: solo se registran pagos nuevos si el estado del caso lo permite.
        # (self.pk is None = pago nuevo; los pagos antiguos del caso se conservan)
        if self.pk is None and self.caso_id and not self.caso.estado.permite_pagos:
            raise ValidationError(
                f'No se puede registrar el pago: el caso {self.caso.codigo} está en estado '
                f'"{self.caso.estado}" y ese estado no permite pagos.'
            )


class PerfilAbogado(models.Model):
    # Uno a uno: cada usuario abogado tiene un solo perfil.
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    numero_colegiatura = models.CharField('número de colegiatura', max_length=20, unique=True)
    especialidad = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'perfil de abogado'
        verbose_name_plural = 'perfiles de abogado'

    def __str__(self):
        return f'{self.usuario.get_full_name() or self.usuario.username} (CAL {self.numero_colegiatura})'
