from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators  import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework  import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Course, Module, Lesson, Enrollment, LessonProgress
from .serializers import(
    CourseListSerializer, CourseDetailSerializer, ModuleSerializer, LessonSerializer,
    EnrollmentSerializer, LessonProgressSerializer, UserSerializer, UserRegistrationSerializer
    )
from users.models import User

class RegistrationView(generics.CreateAPIView):
    """User Registration Endpoint"""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom Jwt token View with additional user data"""

    def post(self, request, *args, **kwargs):
        response =  super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data.get('username'))
            response.data['user'] = UserSerializer(user).data
        return response

#User views
class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get or updata user Profile"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

#Course View
class CourseListView(generics.ListAPIView):
    """List all published courses with filtering"""
serializer_class = CourseListSerializer
permission_classes = [IsAuthenticatedOrReadOnly]
filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
filterset_fields =['level', 'is_free', 'is_published', 'category']
search_fields = ['title', 'description', 'short_description', 'tags']
ordering_fields = ['created_at', 'title', 'price', 'enrolled_count', 'rating']
ordering = ['-created_at']

def get_queryset(self):
    queryset = Course.objects.filter(is_published=True)

    queryset =queryset.annotate(
        module_count=Count('modules'),
        lesson_count=Count('modules__lessons'),
        total_duration=Count('modules__Lesson__duratiion')
     )
     #filter by instructor
    instructor = self.request.query_params.get('instructor')
    if instructor:
        queryset = queryset.filter(instructor__username=instructor)
    return queryset

class CourseDetailView(generics.RetrieveUpdateAPIView):
    """Get detailed course information"""
    serializer_class = CourseDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        return Course.objects.filter(is_published=True)

class CourseViewSet(viewsets.ModelViewSet):
    """Complete Course CRUD Operation"""
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['level', 'is_free', 'is_published', 'is_featured']
    searh_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'title', 'price', 'enrolled_count']

    def get_serializer_class(self):
        if self.action == 'list':
          return CourseDetailSerializer
        return CourseDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        #Instructor unpublished courses
        if self.request.user.is_authenticated and self.request.user.is_instructor:
            if self.action in ['list', 'retrieve']:
                return queryset.filter(
                    Q(is_published=True) | Q(instructor=self.request.user)
                )
 
         # Students and public only see published        
        return queryset.filter(is_published=True)

    def perform_create(self, serializer):
        """Set Intructor to current user on create"""
        serializer.save(instructor=self.request.user)

    @action(detail=True, methods=['post'])
    def enroll(self, request, slug=None):
        """Enroll current user inthis course"""
        course = self.get_object()

        #Check if already enrolled
        if Enrollment.objects.filter(student=request.user, course=course).exist():
            return Response(
                {'detail': 'Already enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )

        #create enrollment
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course,
            status='active'
        )

        #update course enrolled count
        course.enrolled_count += 1
        course.save()

        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def modules(self, request, slug=None):
        """Get all modules for this course"""

        course = self.get_object()
        modules = course.modules.all().order_by('order')
        serializer = ModuleSerializer(modules, many=True)
        return Response(serializer.data)

#Module Views
class ModuleListView(generics.ListAPIView):
    """List all modules for a course"""
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        course_slug = self.kwargs.get('course_slug')
        course = get_object_or_404(Course, slug=course_slug, is_published=True)
        return course.modules.all().order_by('order')

class ModuleDetailView(generics.RetrieveAPIView):
    """Get module details with lessons"""

    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'order'

    def get_queryset(self):
        course_slug = self.kwargs.get('course_slug')
        course = get_object_or_404(Course, slug=course_slug, is_published=True)
        return Module.objects.filter(course=course)

#Lesson Views
class LessonDetailView(generics.RetrieveAPIView):
    """get lesson details"""
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        course_slug = self.kwargs.get('course_slug')
        module_order = self.kwargs.get('module_order')
        course = get_object_or_404(Course, slug=course_slug, is_published=True)
        module = get_object_or_404(Module, course=course, order=module_order)
        return Lesson.objects.filter(module=module)

    def get_object(self):
        lesson_order = self.kwargs.get('lesson_order')
        return get_object_or_404(self.get_queryset(), order=lesson_order)

#Enrollment views'
class EnrollmentListView(generics.ListAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user)

class EnrollmentDetailView(generics.RetrieveUpdateAPIView):
    """Get or update enrollment details"""

    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user)

#Lesson progress view
class LessonProgressView(generics.RetrieveUpdateAPIView):
    """Get or update lesson progress"""
    serializer_class = LessonProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LessonProgress.objects.filter(
            enrollment__student=self.request.user
        )
    def get_object(self):
        """Get progress for specific lesson"""
        enrollment_id = self.kwargs.get('enrollment_id')
        lesson_id = self.kwargs.get('lesson_id')
        return get_object_or_404(
            LessonProgress,
            enrollment_id=enrollment_id,
            lesson_id=lesson_id,
            enrollment__student=self.request.user
        )    
    def perform_update(self, serializer):
        """Update progress and check for completion"""
        serializer.save()

        if serializer.instance.is_completed:
            serializer.instance.enrollment.update_progress()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_lesson_complete_api(request, lesson_id):
    """API endpoint to mark a lesson as complete"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course

    #check if enrolled
    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course
    )

    #update progress
    progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson

    )

    if not progress.is_completed:
        progress.complete_lesson()

    return Response({
        'success': True,
        'progress': enrollment.progress_percentage,
        'completed': progress.is_completed
    })

#dashboard view

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_api(request):
    """API endpoint for user dashboard"""

    #enrollments
    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related('course')

    #statistics
    total_courses = enrollments.count()
    completed_courses = enrollments.filter(status='completed').count()
    in_progress_courses = enrollments.filter(status='active').count()
    avg_progress = enrollments.aggregate(Avg('progress_percentage'))['progress_percentage_avg'] or 0

    #recent activity
    recent_completions = LessonProgress.objects.filter(
        enrollments__student=request.user,
        is_completed=True
    ).select_related('lesson', 'enrollment__course').order_by('-completed_at')[:5]

    #recommended courses
    enrolled_course_ids = enrollments.values_list('course_id', flat=True)
    recommended_courses = Course.objects.filter(
        is_published=True
    ).exclude(
        id__in=enrolled_course_ids
    ).annotate(
        student_count=Count('students')
    ).order_by('-student_count')[:6]

    return Response({
        'statistics':{
            'total_courses': total_courses,
            'completed_courses': completed_courses,
            'in_progress_courses': in_progress_courses,
            'average_progress': round(avg_progress)
        },
        'enrollments': EnrollmentSerializer(enrollments, many=True).data,
        'recent_completions': [
            {
                'lesson': progress.lesson.title,
                'course': progress.enrollment.course.title,
                'completed_at': progress.completed_at
            }
            for progress in recent_completions
        ],
        'recommended_courses': CourseListSerializer(recommended_courses, many=True).data
    })
    