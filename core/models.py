from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.conf import settings
from django.core.exceptions import ValidationError
from .validators import PHONE_VALIDATOR, GHANA_CARD_VALIDATOR
from .managers import CustomUserManager


class Tenant(models.Model):
    TENANT_TYPE = [
        ('basic', 'Basic School'),
        ('shs', 'Senior High School (SHS)'),
        ('technical', 'Technical/Vocational School'),
        ('combined', 'Combined School (Multiple Levels)'),
    ]

    REGION_CHOICES = [
        ('greater_accra', 'Greater Accra'),
        ('ashanti', 'Ashanti'),
        ('western', 'Western'),
        ('eastern', 'Eastern'),
        ('central', 'Central'),
        ('volta', 'Volta'),
        ('northern', 'Northern'),
        ('upper_east', 'Upper East'),
        ('upper_west', 'Upper West'),
        ('bono', 'Bono'),
        ('ahafo', 'Ahafo'),
        ('bono_east', 'Bono East'),
        ('north_east', 'North East'),
        ('savannah', 'Savannah'),
        ('oti', 'Oti'),
        ('western_north', 'Western North'),
    ]

    OWNERSHIP_CHOICES = [
        ('public', 'Public/Government'),
        ('private', 'Private'),
        ('mission', 'Mission/Religious'),
        ('international', 'International'),
    ]

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10, unique=True,
                            help_text="Short code for the school (e.g., TIA)")
    tenant_type = models.CharField(max_length=20, choices=TENANT_TYPE)
    ownership = models.CharField(max_length=20, choices=OWNERSHIP_CHOICES)

    digital_address = models.CharField(
        "Ghana Post Digital Address", max_length=50, blank=True, null=True)
    physical_address = models.CharField(max_length=255, blank=True, null=True)

    # Contact information
    headmaster_name = models.CharField(
        "Headmaster/Principal Name", max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    # School details
    logo = models.ImageField(upload_to='tenant_logos/', blank=True, null=True)
    motto = models.CharField(max_length=255, blank=True, null=True)

    is_active = models.BooleanField(default=True)


class User(AbstractUser, PermissionsMixin):
    USER_TYPES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    is_active_portal = models.BooleanField(default=True, help_text="Portal access status")
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    email = models.EmailField(unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] 
    
    updated_at = models.DateTimeField(auto_now=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    
    # Use our custom manager
    objects = CustomUserManager()
    
    def __str__(self):
        """Dynamically display name based on user profile"""
        try:
            if self.user_type == 'teacher' and hasattr(self, 'teacher'):
                return f"{self.teacher.full_name} (Teacher)"
            elif self.user_type == 'student' and hasattr(self, 'student'):
                return f"{self.student.full_name} (Student)"
            elif self.user_type == 'admin':
                # For admin, use the built-in first_name, last_name or email
                if self.first_name and self.last_name:
                    return f"{self.first_name} {self.last_name} (Admin)"
                elif self.get_full_name():
                    return f"{self.get_full_name()} (Admin)"
                else:
                    return f"{self.email} (Admin)"
            else:
                # Fallback for users without profiles
                return self.email
        except:
            # Fallback in case of any errors
            return self.email
    
    def is_admin(self):
        return self.user_type == 'admin'

    def is_teacher(self):
        return self.user_type == 'teacher'

    def is_student(self):
        return self.user_type == 'student'

    def get_profile(self):
        """Get the associated profile object"""
        try:
            if self.user_type == 'teacher' and hasattr(self, 'teacher'):
                return self.teacher
            elif self.user_type == 'student' and hasattr(self, 'student'):
                return self.student
            return None
        except:
            return None
    
    def get_profile_display_name(self):
        """Get display name from profile or fallback to email"""
        profile = self.get_profile()
        if profile and hasattr(profile, 'full_name'):
            return profile.full_name
        elif self.get_full_name():
            return self.get_full_name()
        return self.email
    
    def get_profile_id(self):
        """Get the ID from the associated profile"""
        profile = self.get_profile()
        if profile:
            if hasattr(profile, 'employee_id'):
                return profile.employee_id
            elif hasattr(profile, 'student_id'):
                return profile.student_id
        return None
    
    @property
    def display_role(self):
        """Get capitalized role for display"""
        return self.get_user_type_display()
    
    def can_login(self):
        """Check if user can login (active and has portal access)"""
        return self.is_active and self.is_active_portal
    
    def reset_password_to_auto_generated(self):
        """Reset password to a new auto-generated one (for teachers/students only)"""
        if self.user_type in ['teacher', 'student']:
            from .managers import CustomUserManager
            manager = CustomUserManager()
            new_password = manager._generate_secure_password()
            self.set_password(new_password)
            self.save()
            return new_password
        else:
            raise ValueError("Auto-password reset only available for teachers and students")
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class Person(models.Model):
    GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'))

    # school field is inherited from TenantAwareMixin
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(class)s_profile",
        blank=True, null=True
    )
    first_name = models.CharField(
        max_length=100, validators=[MinLengthValidator(2)])
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, validators=[
                                 MinLengthValidator(2)])
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    phone = models.CharField(max_length=15, blank=True,
                             null=True, validators=[PHONE_VALIDATOR])
    address = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=128, blank=True, null=True)
    ghana_card_number = models.CharField(
        max_length=15, unique=True, blank=True,
        null=True, validators=[GHANA_CARD_VALIDATOR])
    is_active = models.BooleanField(default=True)

        # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def get_full_name(self):
        return ' '.join(
            filter(None, [self.first_name, self.middle_name, self.last_name])
        )

    def clean(self):
        if self.date_of_birth and self.date_of_birth > timezone.now().date():
            raise ValidationError(
                {"date_of_birth": "Date of birth cannot be in the future"})

    def __str__(self):
        return self.get_full_name()
