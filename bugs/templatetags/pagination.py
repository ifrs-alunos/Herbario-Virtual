# Content of core/templatetags/pagination.py

from django import template

register = template.Library()

@register.inclusion_tag("herbarium/pagination.html", takes_context=True)
def pagination(context, extremes_count=1, expansion=2):

    filters = context["request"].GET.copy()
    if 'page' in filters:
        filters.pop("page")

    paginator = context["paginator"]
    page_obj = context["page_obj"]
    start_ellipse = max(2, page_obj.number - expansion)
    end_ellipse = min(paginator.num_pages, page_obj.number + expansion + 1)
    ellipse_range = range(start_ellipse, end_ellipse)

    return {
        'paginator': paginator,
        'page_obj': page_obj,
        'filters': filters.urlencode(),
        'ellipsed_start': start_ellipse != 2,
        'ellipse_range': ellipse_range,
        'ellipsed_end': end_ellipse != paginator.num_pages,
        'start_pages': range(min(extremes_count, paginator.num_pages)),
        'end_pages': range(max(0, paginator.num_pages-extremes_count), paginator.num_pages),
    }