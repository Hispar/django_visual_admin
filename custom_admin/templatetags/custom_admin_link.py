from django import template

register = template.Library()


@register.inclusion_tag('custom_admin/templatetags/link.html')
def custom_admin_link(url: str, css_class: str, text: str, icon_class: str | None):
    return {
        'url': url,
        'css_class': css_class,
        'text': text,
        'icon_class': icon_class,
    }
