from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
#api documentation
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
# Import views from the apps
from users.views import api_home, dashboard, profile, register
from courses import views as course_views

#api schema view
schema_view = get_schema_view(
    openapi.Info(
        title="LMS API Documentation",
        default_version='v1',
        description="Learning Management System API",
        terms_of_service="https://www.google.com/policies/terms",
        contact=openapi.Contact(email="contact@lms.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Home page
    path('', course_views.course_list, name='home'),
    
    # Course URLs
    path('courses/', course_views.course_list, name='course_list'),
    path('courses/<slug:slug>/', course_views.course_detail, name='course_detail'),
    path('courses/<slug:course_slug>/module/<int:module_order>/lesson/<int:lesson_order>/', 
         course_views.lesson_detail, name='lesson_detail'),
    path('courses/<slug:course_slug>/lesson/<int:lesson_id>/complete/', 
         course_views.mark_lesson_complete, name='mark_lesson_complete'),
    path('courses/<slug:course_slug>/lesson/<int:lesson_id>/quiz/', 
         course_views.save_quiz_result, name='save_quiz_result'),
    
    # User URLs
    path('dashboard/', dashboard, name='dashboard'),
    path('profile/', profile, name='profile'),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', register, name='register'),
    
    # API URLs
    path('api/', include('courses.api_urls')),
    path('api/root/', api_home, name='api-home'),

    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='api-redoc'),

]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)