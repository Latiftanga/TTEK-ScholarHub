# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from django.contrib.auth import get_user_model

User = get_user_model()


def signup_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST.get('password', '').strip()
        user_type = request.POST['user_type']
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'auth/signup.html')
        
        try:
            if user_type in ['teacher', 'student'] and not password:
                # Auto-generate password for teacher/student
                user, generated_password = User.objects.create_user_with_generated_password(
                    email=email,
                    user_type=user_type,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Send email with generated password
                send_password_email(user, generated_password)
                
                messages.success(
                    request, 
                    f'{user_type.title()} account created successfully! '
                    f'Login credentials have been sent to {email}'
                )
                return redirect('login')
                
            else:
                # For admin or when password is provided
                if not password:
                    messages.error(request, 'Password is required for admin accounts')
                    return render(request, 'auth/signup.html')
                
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    user_type=user_type,
                    first_name=first_name,
                    last_name=last_name
                )
                
                login(request, user)
                return redirect('dashboard')
                
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
    
    return render(request, 'auth/signup.html')

def send_password_email(user, password):
    """Send email with login credentials"""
    subject = f'Your {user.get_user_type_display()} Account - School Management System'
    message = f"""
    Hello {user.get_full_name() or user.email},

    Your {user.get_user_type_display().lower()} account has been created successfully.

    Login Credentials:
    Email: {user.email}
    Password: {password}

    Please login at: http://localhost:8000/login/
    
    For security reasons, please change your password after first login.

    Best regards,
    School Management Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def signin_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if user.can_login():  # Using your custom method
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Your account is not active')
        else:
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'auth/signin.html')

@login_required
def dashboard_view(request):
    return render(request, 'auth/dashboard.html', {'user': request.user})