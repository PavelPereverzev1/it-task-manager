from django import template

register = template.Library()


@register.filter
def smart_page_range(page_obj):

    if not page_obj or not hasattr(page_obj, "paginator"):
        return []

    return page_obj.paginator.get_elided_page_range(
        number=page_obj.number,
        on_each_side=2,
        on_ends=1,
    )
