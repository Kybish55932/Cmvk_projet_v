# viewlist/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from inspector.models import Inspector

@login_required
def all_violations_list(request):
    """
    Страница просмотра всего списка нарушений.
    Показываем все колонки, КРОМЕ: 'старший смены' (supervisor) и 'кем выявлено' (tehnick/inspector).
    Статус не показываем и не фильтруем.
    Фильтры: дата от/до, аэропорт (select), служба (multiselect), вид нарушения (multiselect), кто нарушил (text).
    """

    qs = Inspector.objects.all().order_by("-date", "-id")

    # ---- Получаем значения фильтров из GET ----
    date_from = request.GET.get("dateFrom") or ""
    date_to   = request.GET.get("dateTo") or ""
    airport   = request.GET.get("airport") or ""
    services  = request.GET.getlist("service")  # мультиселект
    vtypes    = request.GET.getlist("violation")  # мультиселект
    offender  = request.GET.get("offender") or ""

    # ---- Применяем фильтры ----
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    if airport:
        qs = qs.filter(airport=airport)
    if services:
        qs = qs.filter(service__in=services)
    if vtypes:
        qs = qs.filter(violation__in=vtypes)
    if offender:
        qs = qs.filter(offender__icontains=offender)

    # ---- Справочники для выпадающих списков ----
    # Примечание: service/violation у тебя могут храниться строками,
    # здесь берём distinct по точным значениям.
    airports_choices  = (
        Inspector.objects.exclude(airport="")
        .values_list("airport", flat=True).distinct().order_by("airport")
    )
    services_choices  = (
        Inspector.objects.exclude(service="")
        .values_list("service", flat=True).distinct().order_by("service")
    )
    violations_choices = (
        Inspector.objects.exclude(violation="")
        .values_list("violation", flat=True).distinct().order_by("violation")
    )

    context = {
        "violations": qs,                 # данные таблицы
        "date_from": date_from,
        "date_to": date_to,
        "selected_airport": airport,
        "selected_services": services,
        "selected_violations": vtypes,
        "offender_query": offender,

        "airports_choices": airports_choices,
        "services_choices": services_choices,
        "violations_choices": violations_choices,
    }
    return render(request, "viewlist/list.html", context)
