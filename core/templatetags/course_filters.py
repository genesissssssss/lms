# core/templatetags/course_filters.py
from django import template

register = template.Library()

@register.filter
def enrollment_percentage(enrollment_count, max_students=10):
    """Calculate enrollment percentage for progress bar"""
    if not enrollment_count:
        return 0
    percentage = (enrollment_count / max_students) * 100
    # Cap at 100%
    return min(percentage, 100)

@register.filter
def materials_count(course):
    """Get materials count for a course"""
    return course.materials.count()

@register.filter
def videos_count(course):
    """Get videos count for a course"""
    return course.videos.count()