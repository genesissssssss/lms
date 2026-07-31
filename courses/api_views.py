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

    