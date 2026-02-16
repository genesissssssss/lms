from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os

class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    duration = models.IntegerField(help_text="Duration in hours")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    @property
    def enrolled_students_count(self):
        return self.enrollments.count()
    
    @property
    def materials_count(self):
        return self.materials.count()
    
    @property
    def videos_count(self):
        return self.videos.count()

class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    progress = models.IntegerField(default=0, help_text="Progress percentage")
    
    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"

def material_upload_path(instance, filename):
    return f'course_materials/{instance.course.id}/{filename}'

class CourseMaterial(models.Model):
    MATERIAL_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('doc', 'Document'),
        ('ppt', 'Presentation'),
        ('zip', 'Archive'),
        ('other', 'Other'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    material_type = models.CharField(max_length=10, choices=MATERIAL_TYPE_CHOICES)
    file = models.FileField(upload_to=material_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title
    
    @property
    def filename(self):
        return os.path.basename(self.file.name)

def video_upload_path(instance, filename):
    return f'course_videos/{instance.course.id}/{filename}'

class CourseVideo(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_file = models.FileField(upload_to=video_upload_path, null=True, blank=True)
    video_url = models.URLField(blank=True, help_text="Or provide a YouTube/Vimeo URL")
    duration = models.IntegerField(help_text="Duration in minutes", default=0)
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    @property
    def is_external(self):
        return bool(self.video_url)