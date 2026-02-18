from django.urls import path
from . import views

urlpatterns = [
    # Home and basic pages
    path('', views.HomeView.as_view(), name='home'),
    
    # Student dashboard
    path('student/dashboard/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    
    # Admin dashboard
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    
    # Courses
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/<int:course_id>/enroll/', views.EnrollCourseView.as_view(), name='enroll_course'),
    
    # Admin course management
    path('admin/courses/new/', views.CourseCreateView.as_view(), name='course_create'),
    path('admin/courses/<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_update'),
    path('admin/courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    
    # Materials and videos
    path('admin/courses/<int:course_id>/add-material/', views.AddMaterialView.as_view(), name='add_material'),
    path('admin/courses/<int:course_id>/add-video/', views.AddVideoView.as_view(), name='add_video'),
    
    # User management
    path('admin/users/', views.ManageUsersView.as_view(), name='manage_users'),
    path('admin/student/<int:pk>/analytics/', views.StudentAnalyticsView.as_view(), name='student_analytics'),

    path('admin/courses/new/', views.CourseCreateView.as_view(), name='course_create'),
    path('admin/courses/<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_update'),
    path('admin/courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    
    # Materials and videos
    path('admin/courses/<int:course_id>/add-material/', views.AddMaterialView.as_view(), name='add_material'),
    path('admin/courses/<int:course_id>/add-video/', views.AddVideoView.as_view(), name='add_video'),
    
    # User management
    path('admin/users/', views.ManageUsersView.as_view(), name='manage_users'),
    path('admin/student/<int:pk>/analytics/', views.StudentAnalyticsView.as_view(), name='student_analytics'),
    
    # Student Achievements
    path('student/achievements/', views.StudentAchievementsView.as_view(), name='student_achievements'),
    
    path('admin/enrollments/', views.ManageEnrollmentsView.as_view(), name='manage_enrollments'),
    # Admin Analytics
    path('admin/analytics/students/', views.StudentAnalyticsView.as_view(), name='student_analytics'),

    # Student Analytics (Admin view)
    path('admin/analytics/students/', views.AdminStudentAnalyticsView.as_view(), name='admin_student_analytics'),
]
