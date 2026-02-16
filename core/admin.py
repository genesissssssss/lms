from django.contrib import admin
from .models import Course, Enrollment, CourseMaterial, CourseVideo

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'level', 'price', 'is_published', 'enrolled_students_count')
    list_filter = ('level', 'is_published', 'created_at')
    search_fields = ('title', 'description', 'instructor__username')
    list_editable = ('is_published', 'price')
    filter_horizontal = ()
    raw_id_fields = ('instructor',)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'progress', 'enrolled_at')
    list_filter = ('status', 'enrolled_at')
    search_fields = ('student__username', 'course__title')

class CourseMaterialInline(admin.TabularInline):
    model = CourseMaterial
    extra = 1

class CourseVideoInline(admin.TabularInline):
    model = CourseVideo
    extra = 1

class CourseDetailAdmin(admin.ModelAdmin):
    inlines = [CourseMaterialInline, CourseVideoInline]

admin.site.register(CourseMaterial)
admin.site.register(CourseVideo)