import requests
from django.shortcuts import render

def flights_list(request):
    url = "http://212.112.120.220/csp/adp/json/prilrus.asp"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        flights = response.json()   # тут сразу список словарей
    except Exception as e:
        flights = []
        print("Ошибка при получении JSON:", e)

    # добавляем новый столбец (пример)
    for fli in flights:
        fli["Комментарий"] = "Обновлено с сервера"

    return render(request, "flights/flights.html", {"flights": flights})
from django.shortcuts import render
from .models import Service

def flight_create(request):
    services = Service.objects.all()
    return render(request, "flights/flight_form.html", {"services": services})


# Create your views here.
