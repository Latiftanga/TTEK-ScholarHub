from django.template import Library
from home.models import SchoolSettings

register = Library() 

@register.inclusion_tag('includes/header.html') 
def header_view(request):
    branding = SchoolSettings.objects.first()
    if branding:
        color = branding.color
        logo = branding.logo
    else:
        color = None
        logo = None
 
    context = {
        'request' : request,
        'color' : color,
        'logo' : logo
    }
    return context