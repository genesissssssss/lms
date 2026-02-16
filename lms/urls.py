from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # IMPORTANT: Include core.urls FIRST before Django admin
    path('', include('core.urls')),  # This includes your admin/dashboard/
    
    # Django admin
    path('admin/', admin.site.urls),  # This is now second
    
    # Accounts
    path('accounts/', include('accounts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)