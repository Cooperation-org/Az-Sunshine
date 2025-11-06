"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.utils import timezone


def health_check(request):
    return JsonResponse({"status": "healthy", "timestamp": timezone.now().isoformat()})


urlpatterns = [
    # ==================== Health Check ====================
    path('health/', health_check, name='health_check'),
    
    # ==================== ADMIN ====================
    path('admin/', admin.site.urls),
    
    # ==================== API ====================
    # API v1 - includes all transparency app endpoints
    path('api/v1/', include('transparency.urls', namespace='transparency')),
    
    # Redirect /api/ to /api/v1/ for convenience
    path('api/', RedirectView.as_view(url='/api/v1/', permanent=False)),
    
    # ==================== AUTHENTICATION ====================
    # Django REST Framework browsable API login/logout
    path('api-auth/', include('rest_framework.urls')),
]

# ==================== DEVELOPMENT ONLY ====================
# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ==================== ADMIN CUSTOMIZATION ====================
admin.site.site_header = "Arizona Sunshine Transparency Admin"
admin.site.site_title = "AZ Sunshine Admin"
admin.site.index_title = "Campaign Finance Transparency Dashboard"

