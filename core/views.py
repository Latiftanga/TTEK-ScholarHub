from django.shortcuts import render

def dashboard(request):
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        # Return only the content for HTMX (SPA-like behavior)
        return render(request, 'core/dashboard_content.html')
    
    # Return full page for direct visits
    return render(request, 'core/dashboard.html')