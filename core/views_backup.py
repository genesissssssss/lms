from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Count, Avg, Q
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import Course, Enrollment, CourseMaterial, CourseVideo
from accounts.models import UserProfile
from .forms import CourseForm

class HomeView(TemplateView):
    """Home page view"""
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get featured courses
        context['featured_courses'] = Course.objects.all()[:3]
        return context

class StudentDashboardView(LoginRequiredMixin, TemplateView):
    """Student dashboard view"""
    template_name = 'dashboard/student_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get enrolled courses
        enrolled_courses = Enrollment.objects.filter(
            student=user
        ).select_related('course').order_by('-enrolled_at')
        context['enrolled_courses'] = enrolled_courses
        
        # Get available courses (not enrolled)
        enrolled_course_ids = enrolled_courses.values_list('course_id', flat=True)
        context['available_courses'] = Course.objects.exclude(
            id__in=enrolled_course_ids
        )[:6]
        
        # Calculate statistics
        context['total_enrolled'] = enrolled_courses.count()
        context['completed_courses'] = enrolled_courses.filter(status='completed').count()
        context['in_progress_courses'] = enrolled_courses.filter(status='in_progress').count()
        
        # Calculate overall progress
        if enrolled_courses.exists():
            total_progress = sum(enrollment.progress or 0 for enrollment in enrolled_courses)
            context['overall_progress'] = round(total_progress / enrolled_courses.count())
        else:
            context['overall_progress'] = 0
        
        return context

class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin dashboard view"""
    template_name = 'dashboard/admin_dashboard.html'
    
    def test_func(self):
        user_profile = getattr(self.request.user, 'userprofile', None)
        return user_profile and user_profile.role == 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Platform statistics
        context['total_users'] = User.objects.count()
        context['total_courses'] = Course.objects.count()
        context['total_enrollments'] = Enrollment.objects.count()
        
        # Recent enrollments
        context['recent_enrollments'] = Enrollment.objects.select_related(
            'student', 'course'
        ).order_by('-enrolled_at')[:10]
        
        # Recent users
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        
        # System status
        context['system_status'] = 'Operational'
        
        return context

class CourseListView(ListView):
    """List all courses"""
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Safe annotation - check if field exists first
        try:
            # Try with enrollments (plural)
            queryset = queryset.annotate(
                enrollment_count=Count('enrollments')
            )
        except:
            try:
                # Fallback to enrollment_set
                queryset = queryset.annotate(
                    enrollment_count=Count('enrollment_set')
                )
            except:
                # If both fail, just return the queryset
                pass
        return queryset

class CourseDetailView(DetailView):
    """Course detail view"""
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        
        # Check if user is enrolled
        if self.request.user.is_authenticated:
            context['is_enrolled'] = Enrollment.objects.filter(
                student=self.request.user, 
                course=course
            ).exists()
        else:
            context['is_enrolled'] = False
        
        # Get course materials and videos
        context['materials'] = course.coursematerial_set.all()
        context['videos'] = course.coursevideo_set.all()
        
        return context

class EnrollCourseView(LoginRequiredMixin, DetailView):
    """Enroll in a course"""
    model = Course
    template_name = 'courses/enroll_course.html'
    
    def get(self, request, *args, **kwargs):
        course = self.get_object()
        user = request.user
        
        # Check if already enrolled
        if not Enrollment.objects.filter(student=user, course=course).exists():
            Enrollment.objects.create(
                student=user,
                course=course,
                status='enrolled',
                progress=0
            )
            messages.success(request, f'Successfully enrolled in {course.title}')
        else:
            messages.info(request, f'You are already enrolled in {course.title}')
        
        return redirect('course_detail', pk=course.id)

class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new course"""
    model = Course
    form_class = CourseForm
    template_name = 'admin/course_form.html'
    success_url = reverse_lazy('course_list')
    
    def test_func(self):
        user_profile = getattr(self.request.user, 'userprofile', None)
        return user_profile and user_profile.role in ['admin', 'instructor']
    
    def form_valid(self, form):
        form.instance.instructor = self.request.user
        messages.success(self.request, 'Course created successfully!')
        return super().form_valid(form)

class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update a course"""
    model = Course
    form_class = CourseForm
    template_name = 'admin/course_form.html'
    success_url = reverse_lazy('course_list')
    
    def test_func(self):
        user_profile = getattr(self.request.user, 'userprofile', None)
        if not user_profile:
            return False
        # Admin or course instructor can update
        return user_profile.role == 'admin' or self.get_object().instructor == self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Course updated successfully!')
        return super().form_valid(form)

class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a course"""
    model = Course
    template_name = 'admin/course_confirm_delete.html'
    success_url = reverse_lazy('course_list')
    
    def test_func(self):
        user_profile = getattr(self.request.user, 'userprofile', None)
        return user_profile and user_profile.role == 'admin'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Course deleted successfully!')
        return super().delete(request, *args, **kwargs)

class AddMaterialView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Add material to a course"""
    model = CourseMaterial
    fields = ['title', 'material_type', 'file', 'description']
    template_name = 'admin/add_material.html'
    
    def test_func(self):
        user_profile = getattr(self.request.user, 'userprofile', None)
        if not user_profile:
            return False
        course = get_object_or_404(Course, id=self.kwargs['course_id'])
        return user_profile.role == 'admin' or course.instructor == self.request.user
    
    def form_valid(self, form):
        course = get_object_or_404(Course, id=self.kwargs['course_id'])
        form.instance.course = course
        messages.success(self.request, 'Material added successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('course_detail', kwargs={'pk': self.kwargs['course_id']})

class AddVideoView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Add video to a course"""
    model = CourseVideo
    fields = ['title', 'description', 'video_file', 'video_url', 'duration']
    template_name = 'admin/add_video.html'
    
    def test_func(self):
        user_profile = getattr(self.request.user, 'userprofile', None)
        if not user_profile:
            return False
        course = get_object_or_404(Course, id=self.kwargs['course_id'])
        return user_profile.role == 'admin' or course.instructor == self.request.user
    
    def form_valid(self, form):
        course = get_object_or_404(Course, id=self.kwargs['course_id'])
        form.instance.course = course
        messages.success(self.request, 'Video added successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('course_detail', kwargs={'pk': self.kwargs['course_id']})

class ManageUsersView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Manage users view"""
    model = User
    template_name = 'admin/manage_users.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def test_func(self):
        user_profile = getattr(self.request.user, 'userprofile', None)
        return user_profile and user_profile.role == 'admin'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        # Filter by role
        role_filter = self.request.GET.get('role', '')
        if role_filter:
            queryset = queryset.filter(userprofile__role=role_filter)
        
        return queryset.select_related('userprofile')

class StudentAnalyticsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Student analytics view"""
    model = User
    template_name = 'admin/student_analytics.html'
    context_object_name = 'student'
    
    def test_func(self):
        user_profile = getattr(self.request.user, 'userprofile', None)
        return user_profile and user_profile.role == 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_object()
        
        # Get all enrollments for this student
        enrollments = Enrollment.objects.filter(
            student=student
        ).select_related('course').order_by('-enrolled_at')
        
        context['enrollments'] = enrollments
        context['total_courses'] = enrollments.count()
        context['completed_courses'] = enrollments.filter(status='completed').count()
        
        # Calculate average progress
        if enrollments.exists():
            total_progress = sum(enrollment.progress or 0 for enrollment in enrollments)
            context['average_progress'] = round(total_progress / enrollments.count())
        else:
            context['average_progress'] = 0
        
        # Generate recent activity
        context['recent_activity'] = [
            {
                'type': 'enrollment',
                'description': f'Enrolled in {enrollment.course.title}',
                'timestamp': enrollment.enrolled_at
            }
            for enrollment in enrollments[:5]
        ]
        
        return context
