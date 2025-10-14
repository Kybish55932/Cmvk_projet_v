from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET

from datetime import time, datetime
from collections import defaultdict
import json

from .models import Inspector
from app_direction.decorators import inspector_required
from django.contrib.auth.decorators import login_required

from slujba.models import Service
import json, re





def is_inspector(user):
    return user.groups.filter(name="inspector").exists()

# ------------------- Константы -------------------
AIRPORT_CHOICES = ["Манас", "Ош", "Баткен", "Разаков"]
TYPE_CHOICES = ["Прилет", "Вылет"]
SHIFT_CHOICES = ["1", "2", "3", "4"]


# ------------------- Helpers -------------------
def _payload(request):
    """Принимаем JSON или form-data."""
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body or b"{}")
        except Exception:
            return {}
    return request.POST.dict()


def _parse_hhmm(value):
    """Парсим 'HH:MM' -> time(...) или None."""
    if not value:
        return None
    try:
        hh, mm = value.strip().split(":")
        return time(int(hh), int(mm))
    except Exception:
        return None


# ------------------- CRUD -------------------


@csrf_exempt
@csrf_exempt
def delete_violation(request, id):
    if request.method == "POST":
        v = get_object_or_404(Inspector, id=id)

        # 🚫 Проверяем: если уже согласовано — запретить удаление
        if v.status == "agreed":
            return JsonResponse({
                "error": "Нарушение уже согласовано и не может быть удалено."
            }, status=403)

        v.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid request"}, status=400)

# ------------------- Lists -------------------
@require_GET
def choices(request):
    return JsonResponse({
        "airports": AIRPORT_CHOICES,
        "types": TYPE_CHOICES,
        "shifts": SHIFT_CHOICES,
    })


def inspector_list(request):
    qs = Inspector.objects.all().order_by("-date", "-id")
    data = [{
        "id": v.id,
        "date": v.date.isoformat() if v.date else "",
        "airport": v.airport,
        "flight": v.flight,
        "direction": v.direction,
        "type": v.type,
        "time_start": v.time_start.isoformat(timespec="minutes") if v.time_start else "",
        "time_end": v.time_end.isoformat(timespec="minutes") if v.time_end else "",
        "sector": v.sector,
        "violation_start": v.violation_start.isoformat(timespec="minutes") if v.violation_start else "",
        "violation_end": v.violation_end.isoformat(timespec="minutes") if v.violation_end else "",
        "services": list(v.services.values_list("code", flat=True)),  # ← M2M, правильно
        "violation": v.violation,
        "description": v.description,
        "supervisor": v.supervisor,
        "inspector": v.inspector,
        "shift": v.shift,
        "status": v.status,
    } for v in qs]
    return JsonResponse(data, safe=False)

@login_required
@inspector_required
def inspector_page(request):
    qs = Inspector.objects.all()

    date_from = request.GET.get("dateFrom")
    date_to = request.GET.get("dateTo")
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)

    for field in ["airport", "inspector", "shiftFilter"]:
        value = request.GET.get(field)
        if value:
            field_name = field if field != "shiftFilter" else "shift"
            qs = qs.filter(**{field_name: value})

    svc = request.GET.get("service")
    if svc:
        qs = qs.filter(services__code=svc)  # фильтр по M2M

    return render(request, "inspector/inspector_list.html", {"violations": qs})


def database_page(request):
    violations = Inspector.objects.all().order_by("-date", "-id")
    return render(request, "inspector/database.html", {"violations": violations})


# ------------------- WEEKLY REPORT -------------------
@login_required
def weekly_report_page(request):
    """Страница недельного отчёта"""
    return render(request, "inspector/weekly_report.html")


@csrf_exempt
@login_required
def api_weekly_violations(request):
    start = request.GET.get("start")
    end = request.GET.get("end")

    from datetime import datetime
    # 🔹 Убрали ограничение по source
    qs = (Inspector.objects
          .exclude(status="rejected")  # исключаем только отклонённые
          .order_by("-date"))

    if start and end:
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
            qs = qs.filter(date__range=(start_date, end_date))
        except Exception:
            pass

    data = [{
        "id": v.id,
        "date": v.date.isoformat() if v.date else "",
        "airport": v.airport,
        "flight": v.flight,
        "direction": v.direction,
        "type": v.type,
        "time_start": v.time_start.isoformat(timespec="minutes") if v.time_start else "",
        "time_end": v.time_end.isoformat(timespec="minutes") if v.time_end else "",
        "sector": v.sector,
        "violation_start": v.violation_start.isoformat(timespec="minutes") if v.violation_start else "",
        "violation_end": v.violation_end.isoformat(timespec="minutes") if v.violation_end else "",
        "services": list(v.services.values_list("code", flat=True)),
        "violation": v.violation,
        "description": v.description,
        "status": v.status,
    } for v in qs]
    return JsonResponse({"items": data})


@csrf_exempt
@login_required
def send_for_approval(request, id):
    """Отправка одного нарушения на согласование"""
    try:
        v = Inspector.objects.get(id=id)
        v.status = "sent"
        v.save()
        return JsonResponse({"success": True})
    except Inspector.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)


@csrf_exempt
@login_required
def send_violations(request):
    """Массовая отправка всех нарушений"""
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            ids = data.get("ids", [])
            Inspector.objects.filter(id__in=ids).update(status="sent")
            return JsonResponse({"success": True, "updated_ids": ids})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
@login_required
def send_week(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    import json
    from datetime import datetime
    payload = json.loads(request.body.decode("utf-8"))
    start = datetime.strptime(payload["start"], "%Y-%m-%d").date()
    end = datetime.strptime(payload["end"], "%Y-%m-%d").date()

    updated = (Inspector.objects
    .filter(status="approved", date__range=(start, end))  # убрали source
    .update(status="sent"))
    return JsonResponse({"success": True, "updated": updated})

def _to_codes(val):
    """Принимает list/строку вида: 'АС', 'АС, МСЧ', '["АС","МСЧ"]', '[АС, МСЧ]' → ['АС','МСЧ']"""
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if val is None:
        return []
    s = str(val).strip()
    if not s:
        return []
    # JSON-подобные формы
    try:
        v = json.loads(s.replace("'", '"'))
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
    except Exception:
        pass
    # [АС, МСЧ] / [ "АС" ; "МСЧ" ]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1]
        parts = re.split(r"[,\s;]+", inner)
        return [p.strip(' "\'') for p in parts if p.strip(' "\'')]
    # одиночное значение
    return [s.strip(' "\'')]

@csrf_exempt
@require_http_methods(["POST"])
def add_violation(request):
    data = _payload(request)
    v = Inspector.objects.create(
        date=data.get("date"),
        airport=data.get("airport", ""),
        flight=data.get("flight", ""),
        direction=data.get("direction", ""),
        type=data.get("type", ""),
        time_start=_parse_hhmm(data.get("time_start")),
        time_end=_parse_hhmm(data.get("time_end")),
        sector=data.get("sector", ""),
        violation_start=_parse_hhmm(data.get("violation_start")),
        violation_end=_parse_hhmm(data.get("violation_end")),    # сохраним «сырец» как есть (для совместимости)
        violation=data.get("violation", ""),
        description=data.get("description", ""),
        supervisor=data.get("supervisor", ""),
        inspector=data.get("inspector", ""),
        shift=data.get("shift", ""),
        status=data.get("status", "new"),
        source="inspector",
    )
    # ⬇ СРАЗУ заполним M2M из выбранных кодов
    codes = _to_codes(data.get("service"))
    if codes:
        v.services.set(Service.objects.filter(code__in=codes))
    return JsonResponse({"id": v.id})

@csrf_exempt
@require_http_methods(["POST"])
def edit_violation(request, id):
    v = get_object_or_404(Inspector, id=id)
    if v.status == "agreed":
        return JsonResponse({"error": "Нарушение уже согласовано и не может быть изменено."}, status=403)
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    editable_fields = [
        "date", "airport", "flight", "direction", "type",
        "time_start", "time_end", "sector",
        "violation_start", "violation_end",
        "violation", "description",
        "supervisor", "inspector", "shift", "status"
    ]
    for field in editable_fields:
        if field in data:
            val = data[field]
            if field in ("time_start", "time_end", "violation_start", "violation_end"):
                setattr(v, field, _parse_hhmm(val))
            else:
                setattr(v, field, val or None)

    v.save()

    # ⬇ если прислали поле service — синхронизируем M2M
    if "service" in data:
        codes = _to_codes(data.get("service"))
        if codes:
            v.services.set(Service.objects.filter(code__in=codes))
        else:
            v.services.clear()

    return JsonResponse({"success": True})