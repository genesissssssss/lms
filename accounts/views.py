from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.views.generic import CreateView, FormView
from django.urls import reverse_lazy
from .models import UserProfile

class SignUpView(CreateView):
    """User registration view"""
    form_class = UserCreationForm
    template_name = 'accounts/signup.html'

    def form_valid(self, form):
        # First, save the form to create the user
        user = form.save()
        
        # Create or get user profile
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': 'student'}
        )
        
        # Log the user in
        login(self.request, user)
        messages.success(self.request, 'Account created successfully!')
        
        # Get the profile (use user.userprofile since that's your related_name)
        try:
            profile = user.userprofile
            print(f"SIGNUP: Found profile for {user.username}: role={profile.role}")
        except AttributeError:
            # If signal didn't work, get it from database
            profile = UserProfile.objects.get(user=user)
            print(f"SIGNUP: Retrieved profile from DB for {user.username}")
        
        # Redirect based on role
        if profile.role in ['admin', 'instructor']:
            return redirect('admin_dashboard')
        else:
            return redirect('student_dashboard')
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class SignInView(FormView):
    """User login view"""
    form_class = AuthenticationForm
    template_name = 'accounts/signin.html'
    
    def form_valid(self, form):
        # Get the authenticated user
        user = form.get_user()
        
        # Log the user in
        login(self.request, user)
        messages.success(self.request, f'Welcome back, {user.username}!')
        
        # Get or create profile - MOST RELIABLE METHOD
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': 'admin' if (user.username == 'admin' or user.is_superuser) else 'student'
            }
        )
        
        if created:
            print(f"SIGNIN: Created profile for {user.username} with role={profile.role}")
        else:
            print(f"SIGNIN: Found existing profile for {user.username}: role={profile.role}")
        
        # Debug: Print role for testing
        print(f"SIGNIN: User {user.username} has role: {profile.role}")
        
        # Redirect based on role
        if profile.role in ['admin', 'instructor']:
            print(f"SIGNIN: Redirecting {user.username} to admin_dashboard")
            return redirect('admin_dashboard')
        else:
            print(f"SIGNIN: Redirecting {user.username} to student_dashboard")
            return redirect('student_dashboard')
    
    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password.')
        return super().form_invalid(form)

def signout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')