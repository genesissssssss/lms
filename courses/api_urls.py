from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views 
from .api_views import (
    CourseViewSet, CourseListView, CourseDetailView,
    ModuleListView, ModuleDetailView, LessonDetailView,
    EnrollmentListView, EnrollmentDetailView, LessonProgressView,
    RegisterView, CustomTokenObtainPairView, UserProfileView,
    dashboard_api, mark_lesson_complete_api
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')

urlpatterns = [
    #authentication
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/profile/', UserProfileView.as_view(), name='api-profile'),
    #Dashboard
    path('dashboard/', dashboard_api, name='api-dashboard'),
    #Courses
    path('', include(router.urls)),
    path('courses-list/', CourseListView.as_view(), name='api-course-list'),
    path('courses/<slug:slug>/', CourseDetailView.as_view, name='api-course-detail'),
    #modules
    path('courses/<slug:course_slug>/modules/', ModuleListView.as_view(), name='api-module-list'),
    path('courses/<slug:course_slug>/modules/<int:order>/', ModuleDetailView.as_view(), name='api-module-detail'),
    #lesson
    path('courses/<slug:course_slug>/modules/<int:module_order>/lessons/<int:lesson_order>/', LessonDetailView.as_view(), name='api-lesson-detail'),
    path('lessons/<int:lesson_id>/complete/', mark_lesson_complete_api, name='api-lessons-complete'),
    #enrollments
    path('enrollments/', EnrollmentListView.as_view(), name='api-enrollment-list'),
    path('enrollments/<int:pk>/', EnrollmentDetailView.as_view(), name='api-enrollment-detail'),
    #lesson progress
    path('progress/<int:enrollment_id>/lesson/<int:lesson_id>', LessonProgressView.as_view(), name='api-lesson-progress'),
]