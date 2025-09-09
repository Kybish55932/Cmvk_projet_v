from django.contrib import admin
from .models import Airport, Service, Flight


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "city", "country")
    search_fields = ("name", "code", "city", "country")
    list_filter = ("country",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = (
        "flight_number",
        "departure_airport",
        "arrival_airport",
        "departure_time",
        "arrival_time",
        "service",
        "violation_type",
    )
    search_fields = ("flight_number", "violation_type")
    list_filter = ("departure_airport", "arrival_airport", "service")
    autocomplete_fields = ("departure_airport", "arrival_airport", "service")

