from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class Airport(models.Model):
    """Аэропорты"""
    name = models.CharField(max_length=255, unique=True, verbose_name="Название аэропорта")
    code = models.CharField(max_length=10, unique=True, verbose_name="Код (IATA/ICAO)")
    city = models.CharField(max_length=100, verbose_name="Город")
    country = models.CharField(max_length=100, verbose_name="Страна")

    def __str__(self):
        return f"{self.name} ({self.code})"


class Service(models.Model):
    """Службы аэропорта"""
    name = models.CharField(max_length=255, unique=True, verbose_name="Название службы")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    def __str__(self):
        return self.name


class Flight(models.Model):
    """Рейсы"""
    flight_number = models.CharField(max_length=20, verbose_name="Номер рейса")
    departure_airport = models.ForeignKey(
        Airport, on_delete=models.CASCADE, related_name="departures", verbose_name="Аэропорт вылета"
    )
    arrival_airport = models.ForeignKey(
        Airport, on_delete=models.CASCADE, related_name="arrivals", verbose_name="Аэропорт прилета"
    )
    departure_time = models.DateTimeField(verbose_name="Время вылета (план)")
    arrival_time = models.DateTimeField(verbose_name="Время прилета (план)")
    actual_departure = models.DateTimeField(blank=True, null=True, verbose_name="Фактическое время вылета")
    actual_arrival = models.DateTimeField(blank=True, null=True, verbose_name="Фактическое время прилета")
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ответственная служба"
    )
    violation_type = models.CharField(max_length=255, blank=True, null=True, verbose_name="Вид нарушения")
    violation_details = models.TextField(blank=True, null=True, verbose_name="Детали нарушения")

    def __str__(self):
        return f"{self.flight_number} ({self.departure_airport} → {self.arrival_airport})"


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('specialist', 'специалист'),
        ('adminsration', 'Администрация'),
        ('inspector', 'Испектор'),
        ('head of service', 'Дирекция'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='adminsration')
    created_at = models.DateTimeField(auto_now_add=True)

    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="customuser_set",
        related_query_name="user",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="customuser_set",
        related_query_name="user",
    )


class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    can_view_reports = models.BooleanField(default=False)
    can_edit_reports = models.BooleanField(default=False)
    can_view_all = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.user.get_role_display()}"