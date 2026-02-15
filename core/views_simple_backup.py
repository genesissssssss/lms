
class CourseListView(ListView):
    """List all courses - SIMPLIFIED VERSION"""
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Simple version without annotations to avoid errors
        return queryset
