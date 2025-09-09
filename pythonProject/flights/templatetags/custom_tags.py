from django import template

register = template.Library()

@register.filter
def get_item(obj, key):
    """Возвращает значение по ключу для словаря или атрибут объекта."""
    return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, '')
