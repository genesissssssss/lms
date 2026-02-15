from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Count, Avg, Q, Sum, Max, Min
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import Course, Enrollment, CourseMaterial, CourseVideo
from accounts.models import UserProfile
from .forms import CourseForm, CourseMaterialForm, CourseVideoForm
from django.views import generic
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone
from datetime import timedelta


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

class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, generic.TemplateView): 
    template_name = 'admin/admin_dashboard.html'
    
    def test_func(self):
        """Only allow users with admin role to access this view."""
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.role == 'admin'
    
    def handle_no_permission(self):
        """Redirect non-admin users to their appropriate dashboard."""
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.role == 'student':
                return redirect('student_dashboard')
        return redirect('home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Basic stats
        context['total_users'] = User.objects.count()
        context['total_courses'] = Course.objects.count()
        context['total_enrollments'] = Enrollment.objects.count()
        context['recent_enrollments'] = Enrollment.objects.select_related('student', 'course').order_by('-enrolled_at')[:5]
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        context['system_status'] = 'Operational'
        
        # Get courses - don't try to set additional attributes
        context['courses'] = Course.objects.all()[:10]
        
        return context

class CourseListView(ListView):
    """List all courses"""
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Use enrollments (plural) based on your model
        queryset = queryset.annotate(
            enrollment_count=Count('enrollments')
        )
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
        context['materials'] = course.materials.all()
        context['videos'] = course.videos.all()
        
        return context

class EnrollCourseView(LoginRequiredMixin, View):
    """Enroll in a course"""
    
    def get(self, request, course_id):
        # Get the course
        course = get_object_or_404(Course, id=course_id)
        user = request.user
        
        # Check if user has a profile
        if not hasattr(user, 'userprofile'):
            messages.error(request, 'User profile not found. Please contact support.')
            return redirect('course_detail', pk=course_id)
        
        # Check role - only students can enroll
        if user.userprofile.role == 'admin':
            messages.error(request, 'Admins cannot enroll in courses. Use the admin dashboard to manage courses.')
            return redirect('admin_dashboard')
        elif user.userprofile.role == 'instructor':
            messages.error(request, 'Instructors cannot enroll in courses. You can create and manage courses.')
            return redirect('admin_dashboard')
        
        # Check if already enrolled
        enrollment, created = Enrollment.objects.get_or_create(
            student=user,
            course=course,
            defaults={
                'status': 'enrolled',
                'progress': 0
            }
        )
        
        if created:
            messages.success(request, f'✅ Successfully enrolled in "{course.title}"!')
        else:
            messages.info(request, f'You are already enrolled in "{course.title}"')
        
        return redirect('course_detail', pk=course_id)
    
    def post(self, request, course_id):
        # Handle POST requests the same way
        return self.get(request, course_id)

class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new course"""
    model = Course
    form_class = CourseForm
    template_name = 'admin/course_form.html'
    success_url = reverse_lazy('course_list')
    
    def test_func(self):
        try:
            user_profile = self.request.user.userprofile
            return user_profile.role in ['admin', 'instructor']
        except UserProfile.DoesNotExist:
            return False
    
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
        try:
            user_profile = self.request.user.userprofile
            course = self.get_object()
            # Admin or course instructor can update
            return user_profile.role == 'admin' or course.instructor == self.request.user
        except UserProfile.DoesNotExist:
            return False
    
    def form_valid(self, form):
        messages.success(self.request, 'Course updated successfully!')
        return super().form_valid(form)

class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a course"""
    model = Course
    template_name = 'admin/course_confirm_delete.html'
    success_url = reverse_lazy('course_list')
    
    def test_func(self):
        try:
            user_profile = self.request.user.userprofile
            return user_profile.role == 'admin'
        except UserProfile.DoesNotExist:
            return False
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Course deleted successfully!')
        return super().delete(request, *args, **kwargs)

class ManageUsersView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Manage users view"""
    template_name = 'admin/manage_users.html'
    context_object_name = 'users'
    paginate_by = 10
    
    def test_func(self):
        """Only allow admin users"""
        try:
            return self.request.user.userprofile.role == 'admin'
        except UserProfile.DoesNotExist:
            return False
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        
        # Filter by role if specified
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(userprofile__role=role)
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle role changes"""
        if request.method == 'POST':
            user_id = request.POST.get('user_id')
            new_role = request.POST.get('new_role')
            
            try:
                user = User.objects.get(id=user_id)
                profile = user.userprofile
                profile.role = new_role
                profile.save()
                messages.success(request, f'Updated {user.username} role to {new_role}')
            except User.DoesNotExist:
                messages.error(request, 'User not found')
            except AttributeError:
                messages.error(request, 'User profile not found')
        
        return redirect('manage_users')

class AddMaterialView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = 'admin/add_material.html'
    form_class = CourseMaterialForm
    model = CourseMaterial
    
    def test_func(self):
        """Allow admin and instructor users"""
        try:
            role = self.request.user.userprofile.role
            return role in ['admin', 'instructor']
        except UserProfile.DoesNotExist:
            return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('course_id')
        context['course'] = get_object_or_404(Course, id=course_id)
        return context
    
    def form_valid(self, form):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        form.instance.course = course
        messages.success(self.request, 'Material uploaded successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        course_id = self.kwargs.get('course_id')
        return reverse_lazy('course_detail', kwargs={'pk': course_id})

class AddVideoView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = 'admin/add_video.html'
    form_class = CourseVideoForm
    model = CourseVideo
    
    def test_func(self):
        """Allow admin and instructor users"""
        try:
            role = self.request.user.userprofile.role
            return role in ['admin', 'instructor']
        except UserProfile.DoesNotExist:
            return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs.get('course_id')
        context['course'] = get_object_or_404(Course, id=course_id)
        return context
    
    def form_valid(self, form):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        form.instance.course = course
        messages.success(self.request, 'Video uploaded successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        course_id = self.kwargs.get('course_id')
        return reverse_lazy('course_detail', kwargs={'pk': course_id})

class StudentAnalyticsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Student analytics view"""
    model = User
    template_name = 'admin/student_analytics.html'
    context_object_name = 'student'
    
    def test_func(self):
        try:
            return self.request.user.userprofile.role == 'admin'
        except UserProfile.DoesNotExist:
            return False
    
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
    
    # Add to core/views.py
class ManageEnrollmentsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Manage all enrollments view"""
    model = Enrollment
    template_name = 'admin/manage_enrollments.html'
    context_object_name = 'enrollments'
    paginate_by = 20
    
    def test_func(self):
        """Only allow admin users"""
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.role == 'admin'
    
    def get_queryset(self):
        queryset = Enrollment.objects.select_related('student', 'course').order_by('-enrolled_at')
        
        # Filter by status if specified
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by course if specified
        course_id = self.request.GET.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        # Search by student username
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(student__username__icontains=search)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_enrollments'] = Enrollment.objects.count()
        context['pending_count'] = Enrollment.objects.filter(status='pending').count()
        context['active_count'] = Enrollment.objects.filter(status='enrolled').count()
        context['completed_count'] = Enrollment.objects.filter(status='completed').count()
        context['courses'] = Course.objects.all()
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle enrollment status updates"""
        enrollment_id = request.POST.get('enrollment_id')
        new_status = request.POST.get('status')
        
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
            enrollment.status = new_status
            enrollment.save()
            messages.success(request, f'Enrollment status updated to {new_status}')
        except Enrollment.DoesNotExist:
            messages.error(request, 'Enrollment not found')
        
        return redirect('manage_enrollments')
     
    
class StudentAchievementsView(LoginRequiredMixin, TemplateView):
    """Student achievements view showing progress in enrolled courses"""
    template_name = 'dashboard/achievements.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all enrollments for the student
        enrollments = Enrollment.objects.filter(
            student=user
        ).select_related('course').order_by('-enrolled_at')
        
        # Calculate overall statistics
        total_enrolled = enrollments.count()
        completed_courses = enrollments.filter(status='completed').count()
        in_progress = enrollments.filter(status='enrolled').count()
        
        # Calculate average progress
        if total_enrolled > 0:
            total_progress = sum(enrollment.progress or 0 for enrollment in enrollments)
            average_progress = round(total_progress / total_enrolled)
        else:
            average_progress = 0
        
        # Get recent activity
        recent_activity = []
        for enrollment in enrollments[:5]:
            recent_activity.append({
                'type': 'enrollment',
                'description': f'Enrolled in {enrollment.course.title}',
                'date': enrollment.enrolled_at,
                'course': enrollment.course
            })
        
        # Group courses by progress level
        excellent_progress = enrollments.filter(progress__gte=75).count()
        good_progress = enrollments.filter(progress__gte=50, progress__lt=75).count()
        needs_work = enrollments.filter(progress__lt=50).count()
        
        # Achievement badges data
        achievements = [
            {
                'name': 'Quick Starter',
                'description': 'Enrolled in your first course',
                'icon': '🚀',
                'unlocked': total_enrolled >= 1,
                'progress': 1 if total_enrolled >= 1 else 0,
                'total': 1
            },
            {
                'name': 'Course Collector',
                'description': 'Enrolled in 5 different courses',
                'icon': '📚',
                'unlocked': total_enrolled >= 5,
                'progress': min(total_enrolled, 5),
                'total': 5
            },
            {
                'name': 'Dedicated Learner',
                'description': 'Complete your first course',
                'icon': '🎓',
                'unlocked': completed_courses >= 1,
                'progress': min(completed_courses, 1),
                'total': 1
            },
            {
                'name': 'Course Master',
                'description': 'Complete 3 courses',
                'icon': '🏆',
                'unlocked': completed_courses >= 3,
                'progress': min(completed_courses, 3),
                'total': 3
            },
            {
                'name': 'Progress Champion',
                'description': 'Reach 50% average progress across all courses',
                'icon': '📈',
                'unlocked': average_progress >= 50,
                'progress': min(average_progress, 100),
                'total': 100
            },
            {
                'name': 'Perfect Progress',
                'description': 'Reach 100% progress in any course',
                'icon': '⭐',
                'unlocked': enrollments.filter(progress=100).exists(),
                'progress': 1 if enrollments.filter(progress=100).exists() else 0,
                'total': 1
            },
        ]
        
        context.update({
            'enrollments': enrollments,
            'total_enrolled': total_enrolled,
            'completed_courses': completed_courses,
            'in_progress': in_progress,
            'average_progress': average_progress,
            'recent_activity': recent_activity,
            'excellent_progress': excellent_progress,
            'good_progress': good_progress,
            'needs_work': needs_work,
            'achievements': achievements,
        })
        
        return context
    
    

class StudentAnalyticsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Student analytics view for admin to track student progress"""
    template_name = 'admin/student_analytics.html'
    
    def test_func(self):
        """Only allow admin users"""
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.role == 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        date_range = self.request.GET.get('range', '30')
        student_filter = self.request.GET.get('student', '')
        course_filter = self.request.GET.get('course', '')
        
        # Base queryset
        enrollments = Enrollment.objects.select_related('student', 'course')
        
        # Apply date filter
        if date_range != 'all':
            days = int(date_range)
            cutoff_date = timezone.now() - timedelta(days=days)
            enrollments = enrollments.filter(enrolled_at__gte=cutoff_date)
        
        # Apply student filter
        if student_filter:
            enrollments = enrollments.filter(
                Q(student__username__icontains=student_filter) |
                Q(student__email__icontains=student_filter) |
                Q(student__first_name__icontains=student_filter) |
                Q(student__last_name__icontains=student_filter)
            )
        
        # Apply course filter
        if course_filter:
            enrollments = enrollments.filter(course_id=course_filter)
        
        # Overall Statistics
        total_students = User.objects.filter(userprofile__role='student').count()
        active_students = enrollments.values('student').distinct().count()
        total_enrollments = Enrollment.objects.count()
        completed_courses = Enrollment.objects.filter(status='completed').count()
        
        # Calculate average progress across all enrollments
        all_progress = Enrollment.objects.exclude(progress__isnull=True).values_list('progress', flat=True)
        avg_progress = round(sum(all_progress) / len(all_progress)) if all_progress else 0
        
        # Student performance distribution
        performance_distribution = {
            'excellent': Enrollment.objects.filter(progress__gte=75).count(),
            'good': Enrollment.objects.filter(progress__gte=50, progress__lt=75).count(),
            'average': Enrollment.objects.filter(progress__gte=25, progress__lt=50).count(),
            'struggling': Enrollment.objects.filter(progress__lt=25).count(),
        }
        
        # Top performing students
        top_students = []
        student_progress = Enrollment.objects.values(
            'student__id', 'student__username', 'student__email'
        ).annotate(
            avg_progress=Avg('progress'),
            courses_count=Count('id'),
            completed_count=Count('id', filter=Q(status='completed'))
        ).filter(avg_progress__isnull=False).order_by('-avg_progress')[:5]
        
        for student in student_progress:
            top_students.append({
                'id': student['student__id'],
                'username': student['student__username'],
                'email': student['student__email'],
                'avg_progress': round(student['avg_progress']),
                'courses_count': student['courses_count'],
                'completed_count': student['completed_count'],
            })
        
        # Students needing attention (low progress)
        struggling_students = []
        struggling = Enrollment.objects.values(
            'student__id', 'student__username', 'student__email'
        ).annotate(
            avg_progress=Avg('progress'),
            courses_count=Count('id')
        ).filter(avg_progress__lt=25).order_by('avg_progress')[:5]
        
        for student in struggling:
            struggling_students.append({
                'id': student['student__id'],
                'username': student['student__username'],
                'email': student['student__email'],
                'avg_progress': round(student['avg_progress']),
                'courses_count': student['courses_count'],
            })
        
        # Course popularity
        course_popularity = Course.objects.annotate(
            enrollment_count=Count('enrollments'),
            completed_count=Count('enrollments', filter=Q(enrollments__status='completed')),
            avg_progress=Avg('enrollments__progress')
        ).order_by('-enrollment_count')[:5]
        
        # Monthly enrollment trends
        monthly_enrollments = Enrollment.objects.annotate(
            month=TruncMonth('enrolled_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('-month')[:12]
        
        # Recent activity
        recent_activity = []
        recent_enrollments = Enrollment.objects.select_related(
            'student', 'course'
        ).order_by('-enrolled_at')[:10]
        
        for enrollment in recent_enrollments:
            recent_activity.append({
                'type': 'enrollment',
                'student': enrollment.student.username,
                'course': enrollment.course.title,
                'date': enrollment.enrolled_at,
                'progress': enrollment.progress,
                'status': enrollment.status
            })
        
        context.update({
            'total_students': total_students,
            'active_students': active_students,
            'total_enrollments': total_enrollments,
            'completed_courses': completed_courses,
            'avg_progress': avg_progress,
            'performance_distribution': performance_distribution,
            'top_students': top_students,
            'struggling_students': struggling_students,
            'course_popularity': course_popularity,
            'monthly_enrollments': monthly_enrollments,
            'recent_activity': recent_activity,
            'date_range': date_range,
            'student_filter': student_filter,
            'course_filter': course_filter,
            'courses': Course.objects.all(),
        })
        
        return context