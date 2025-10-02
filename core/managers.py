# dashboard/managers.py
from django.contrib.auth.models import BaseUserManager
import string
import secrets


class CustomUserManager(BaseUserManager):
    """Custom user manager with automatic password generation for teachers and students"""
    
    def _generate_secure_password(self, length=12):
        """Generate a secure, readable password"""
        alphabet = string.ascii_letters + string.digits
        
        while True:
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
            if (any(c.islower() for c in password) and
                any(c.isupper() for c in password) and
                any(c.isdigit() for c in password)):
                return password
    
    def _create_user(self, email, password, **extra_fields):
        """Create and save a user with the given email and password"""
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        if password:
            user.set_password(password)
        else:
            generated_password = self._generate_secure_password()
            user.set_password(generated_password)
            user._generated_password = generated_password
        
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, **extra_fields):
        """Create a regular user"""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_active_portal', True)
        
        user_type = extra_fields.get('user_type', '')
        
        if user_type in ['teacher', 'student'] and not password:
            password = self._generate_secure_password()
            extra_fields['_generated_password'] = password
        
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create a superuser - password is required"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_active_portal', True)
        extra_fields.setdefault('user_type', 'admin')
        
        if not password:
            raise ValueError('Superuser must have a password.')
        
        return self._create_user(email, password, **extra_fields)
    
    def create_user_with_generated_password(self, email, user_type, **extra_fields):
        """Create user with auto-generated password and return both user and password"""
        if user_type not in ['teacher', 'student']:
            raise ValueError('Auto-password generation only for teachers and students')
        
        password = self._generate_secure_password()
        extra_fields['user_type'] = user_type
        
        user = self._create_user(email, password, **extra_fields)
        return user, password