from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Course, Module, Lesson, Enrollment, LessonProgress

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'role', 'bio', 'profile_picture', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 
                  'first_name', 'last_name', 'role']
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for Lesson model"""
    
    is_video = serializers.BooleanField(read_only=True)
    is_text = serializers.BooleanField(read_only=True)
    is_quiz = serializers.BooleanField(read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content_type', 'order', 'description',
                  'is_free_preview', 'video_url', 'duration', 'text_content',
                  'quiz_data', 'passing_score', 'view_count', 'completed_count',
                  'is_video', 'is_text', 'is_quiz', 'completion_percentage',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'view_count', 'completed_count', 
                           'created_at', 'updated_at']
    
    def get_completion_percentage(self, obj):
        return obj.get_completion_percentage()


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for Module model"""
    
    lessons = LessonSerializer(many=True, read_only=True)
    lesson_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'estimated_time',
                  'lesson_count', 'lessons', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for Course list view (minimal)"""
    
    instructor_name = serializers.CharField(source='instructor.username', read_only=True)
    module_count = serializers.IntegerField(read_only=True)
    lesson_count = serializers.IntegerField(read_only=True)
    total_duration = serializers.IntegerField(read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'short_description', 'thumbnail',
                  'level', 'price', 'is_free', 'instructor_name',
                  'module_count', 'lesson_count', 'total_duration',
                  'enrolled_count', 'rating', 'is_published', 'is_featured',
                  'is_enrolled', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_is_enrolled(self, obj):
        """Check if current user is enrolled"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Enrollment.objects.filter(
                student=request.user, 
                course=obj
            ).exists()
        return False


class CourseDetailSerializer(serializers.ModelSerializer):
    """Serializer for Course detail view (full)"""
    
    instructor = UserSerializer(read_only=True)
    modules = ModuleSerializer(many=True, read_only=True)
    enrolled_count = serializers.IntegerField(read_only=True)
    total_modules = serializers.IntegerField(read_only=True)
    total_lessons = serializers.IntegerField(read_only=True)
    total_duration_minutes = serializers.IntegerField(read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    enrollment_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'description', 'short_description',
                  'thumbnail', 'promo_video', 'level', 'category', 'tags',
                  'price', 'is_free', 'instructor', 'modules',
                  'enrolled_count', 'rating', 'review_count',
                  'total_modules', 'total_lessons', 'total_duration_minutes',
                  'is_published', 'is_featured', 'is_enrolled',
                  'enrollment_progress', 'created_at', 'updated_at',
                  'published_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'published_at']
    
    def get_is_enrolled(self, obj):
        """Check if current user is enrolled"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Enrollment.objects.filter(
                student=request.user, 
                course=obj
            ).exists()
        return False
    
    def get_enrollment_progress(self, obj):
        """Get enrollment progress for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = Enrollment.objects.get(
                    student=request.user, 
                    course=obj
                )
                return enrollment.progress_percentage
            except Enrollment.DoesNotExist:
                pass
        return None


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for Enrollment model"""
    
    course = CourseListSerializer(read_only=True)
    course_id = serializers.IntegerField(write_only=True)
    student = UserSerializer(read_only=True)
    
    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'course', 'course_id', 'status',
                  'progress_percentage', 'enrolled_at', 'completed_at',
                  'last_accessed']
        read_only_fields = ['id', 'student', 'enrolled_at', 'last_accessed']


class LessonProgressSerializer(serializers.ModelSerializer):
    """Serializer for LessonProgress model"""
    
    lesson = LessonSerializer(read_only=True)
    lesson_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = LessonProgress
        fields = ['id', 'enrollment', 'lesson', 'lesson_id', 'is_completed',
                  'completed_at', 'last_watched_position', 'time_spent',
                  'quiz_score', 'quiz_answers']
        read_only_fields = ['id', 'enrollment', 'completed_at']