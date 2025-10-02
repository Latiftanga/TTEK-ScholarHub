from django import forms
from django.core.exceptions import ValidationError
from .models import Teacher
from core.models import User
from django.core.mail import send_mail
from django.conf import settings
import random
import string

class TeacherForm(forms.ModelForm):
    """Form for creating/editing a teacher"""
    
    # Optional user account creation
    create_user_account = forms.BooleanField(
        required=False,
        initial=False,
        label="Create User Account",
        help_text="Check to create a portal login account for this teacher"
    )
    
    send_credentials_email = forms.BooleanField(
        required=False,
        initial=True,
        label="Send Credentials via Email",
        help_text="Send login credentials to teacher's email"
    )
    
    class Meta:
        model = Teacher
        fields = [
            'first_name', 'middle_name', 'last_name', 'gender',
            'date_of_birth', 'phone', 'address', 'email',
            'ghana_card_number', 'qualification', 'specialization',
            'employment_status', 'hire_date', 'profile_picture', 'is_active'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'gender': forms.Select(attrs={'class': 'form-input'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'ghana_card_number': forms.TextInput(attrs={'class': 'form-input'}),
            'qualification': forms.Select(attrs={'class': 'form-input'}),
            'specialization': forms.TextInput(attrs={'class': 'form-input'}),
            'employment_status': forms.Select(attrs={'class': 'form-input'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email required
        self.fields['email'].required = True
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        create_account = self.cleaned_data.get('create_user_account')
        
        if email and create_account:
            # Check if user with this email already exists
            if User.objects.filter(email=email).exists():
                raise ValidationError(
                    "A user account with this email already exists."
                )
        
        return email
    
    def save(self, commit=True):
        teacher = super().save(commit=False)
        
        if commit:
            teacher.save()
            
            # Create user account if requested
            if self.cleaned_data.get('create_user_account'):
                self.create_user_for_teacher(teacher)
        
        return teacher
    
    def create_user_for_teacher(self, teacher):
        """Create user account for teacher"""
        email = teacher.email
        
        # Generate random password
        password = self.generate_password()
        
        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            user_type='teacher',
            first_name=teacher.first_name,
            last_name=teacher.last_name
        )
        
        # Link user to teacher
        teacher.user = user
        teacher.save()
        
        # Send credentials email if requested
        if self.cleaned_data.get('send_credentials_email'):
            self.send_credentials_email(teacher, email, password)
        
        return user, password
    
    @staticmethod
    def generate_password(length=12):
        """Generate a secure random password"""
        characters = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choice(characters) for i in range(length))
        return password
    
    @staticmethod
    def send_credentials_email(teacher, email, password):
        """Send login credentials to teacher"""
        subject = 'Your Teacher Portal Login Credentials'
        message = f"""
Hello {teacher.get_full_name()},

Your teacher portal account has been created successfully.

Login Credentials:
------------------
Email: {email}
Password: {password}
Employee ID: {teacher.employee_id}

Please login at: {settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'http://localhost:8000'}

For security reasons, please change your password after first login.

Best regards,
School Management Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@school.com',
            [email],
            fail_silently=False,
        )


class BulkTeacherUploadForm(forms.Form):
    """Form for bulk teacher upload via Excel/CSV"""
    
    file = forms.FileField(
        label="Upload File",
        help_text="Upload .xlsx or .csv file with teacher data",
        widget=forms.FileInput(attrs={'class': 'form-input', 'accept': '.xlsx,.csv'})
    )
    
    create_user_accounts = forms.BooleanField(
        required=False,
        initial=True,
        label="Create User Accounts",
        help_text="Automatically create portal accounts for all teachers"
    )
    
    send_credentials_email = forms.BooleanField(
        required=False,
        initial=True,
        label="Send Credentials via Email",
        help_text="Send login credentials to each teacher's email"
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        
        if file:
            # Check file extension
            if not file.name.endswith(('.xlsx', '.csv')):
                raise ValidationError(
                    "Only .xlsx and .csv files are supported."
                )
            
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError(
                    "File size must be under 5MB."
                )
        
        return file
