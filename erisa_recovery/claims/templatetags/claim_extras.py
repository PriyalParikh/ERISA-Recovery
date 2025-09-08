from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    """Split a string by delimiter"""
    return value.split(delimiter)

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})