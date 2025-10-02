import pandas as pd
from django.core.exceptions import ValidationError
from .models import Teacher
from core.models import User
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings
import random
import string


class BulkTeacherProcessor:
    """Process bulk teacher uploads from Excel/CSV"""
    
    REQUIRED_COLUMNS = [
        'first_name', 'last_name', 'gender', 'date_of_birth',
        'email', 'phone', 'qualification', 'specialization',
        'employment_status', 'hire_date'
    ]
    
    OPTIONAL_COLUMNS = [
        'middle_name', 'address', 'ghana_card_number',
    ]
    
    GENDER_MAP = {
        'M': 'M', 'Male': 'M', 'male': 'M',
        'F': 'F', 'Female': 'F', 'female': 'F'
    }
    
    QUALIFICATION_MAP = {
        'diploma': 'diploma',
        'bachelor': 'bachelor',
        'master': 'master',
        'phd': 'phd',
    }
    
    EMPLOYMENT_STATUS_MAP = {
        'permanent': 'permanent',
        'contract': 'contract',
        'temporary': 'temporary',
    }
    
    def __init__(self, file, create_accounts=True, send_emails=True):
        self.file = file
        self.create_accounts = create_accounts
        self.send_emails = send_emails
        self.errors = []
        self.success_count = 0
        self.created_teachers = []
        self.created_credentials = []
    
    def process(self):
        """Process the uploaded file"""
        try:
            # Read file based on extension
            if self.file.name.endswith('.xlsx'):
                df = pd.read_excel(self.file)
            else:
                df = pd.read_csv(self.file)
            
            # Clean column names (remove extra spaces)
            df.columns = df.columns.str.strip()
            
            # Validate columns
            self.validate_columns(df)
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    self.process_row(row, index + 2)  # +2 for header row and 0-index
                except Exception as e:
                    self.errors.append(f"Row {index + 2}: {str(e)}")
            
            return {
                'success': self.success_count,
                'errors': self.errors,
                'teachers': self.created_teachers,
                'credentials': self.created_credentials
            }
        
        except Exception as e:
            raise ValidationError(f"Error processing file: {str(e)}")
    
    def validate_columns(self, df):
        """Validate that all required columns exist"""
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        
        if missing_columns:
            raise ValidationError(
                f"Missing required columns: {', '.join(missing_columns)}"
            )
    
    def process_row(self, row, row_number):
        """Process a single row"""
        # Prepare data
        teacher_data = {}
        
        # Process all columns
        for column in self.REQUIRED_COLUMNS + self.OPTIONAL_COLUMNS:
            if column in row and pd.notna(row[column]):
                value = row[column]
                
                # Convert dates
                if column in ['date_of_birth', 'hire_date']:
                    value = self.parse_date(value, column)
                
                # Normalize gender
                if column == 'gender':
                    value = self.GENDER_MAP.get(str(value).strip(), value)
                
                # Normalize qualification
                if column == 'qualification':
                    value = self.QUALIFICATION_MAP.get(str(value).strip().lower(), value)
                
                # Normalize employment_status
                if column == 'employment_status':
                    value = self.EMPLOYMENT_STATUS_MAP.get(str(value).strip().lower(), value)
                
                # Clean string values
                if isinstance(value, str):
                    value = value.strip()
                
                teacher_data[column] = value
        
        # Check if teacher with same email exists
        if Teacher.objects.filter(email=teacher_data.get('email')).exists():
            raise ValidationError(f"Teacher with email {teacher_data.get('email')} already exists")
        
        # Create teacher
        teacher = Teacher(**teacher_data)
        teacher.full_clean()  # Validate
        teacher.save()
        
        # Create user account if requested
        credentials = None
        if self.create_accounts and teacher.email:
            credentials = self.create_user_account(teacher)
        
        self.created_teachers.append(teacher)
        self.success_count += 1
    
    def parse_date(self, value, column_name):
        """Parse date from various formats"""
        if isinstance(value, pd.Timestamp):
            return value.date()
        
        if isinstance(value, str):
            # Try different date formats
            formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            
            raise ValidationError(f"Invalid date format in {column_name}: {value}")
        
        return value
    
    def create_user_account(self, teacher):
        """Create user account for teacher"""
        # Check if user already exists
        if User.objects.filter(email=teacher.email).exists():
            self.errors.append(f"User account for {teacher.email} already exists")
            return None
        
        # Generate password
        password = self.generate_password()
        
        try:
            # Create user
            user = User.objects.create_user(
                email=teacher.email,
                password=password,
                user_type='teacher',
                first_name=teacher.first_name,
                last_name=teacher.last_name
            )
            
            # Link user to teacher
            teacher.user = user
            teacher.save()
            
            credentials = {
                'teacher': teacher,
                'email': teacher.email,
                'password': password,
                'employee_id': teacher.employee_id
            }
            
            # Send email if requested
            if self.send_emails:
                self.send_credentials_email(teacher, teacher.email, password)
            
            self.created_credentials.append(credentials)
            
            return credentials
        
        except Exception as e:
            self.errors.append(f"Error creating user for {teacher.email}: {str(e)}")
            return None
    
    @staticmethod
    def generate_password(length=12):
        """Generate a secure random password"""
        characters = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choice(characters) for i in range(length))
        # Ensure at least one of each type
        if not any(c.isupper() for c in password):
            password = password[:-1] + random.choice(string.ascii_uppercase)
        if not any(c.isdigit() for c in password):
            password = password[:-1] + random.choice(string.digits)
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
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@school.com',
                [email],
                fail_silently=False,
            )
        except Exception as e:
            # Log error but don't fail the entire process
            print(f"Error sending email to {email}: {str(e)}")
    
    @staticmethod
    def get_sample_template():
        """Generate a sample Excel template"""
        data = {
            'first_name': ['John', 'Jane'],
            'middle_name': ['Michael', 'Ann'],
            'last_name': ['Doe', 'Smith'],
            'gender': ['M', 'F'],
            'date_of_birth': ['1985-05-15', '1990-08-20'],
            'email': ['john.doe@example.com', 'jane.smith@example.com'],
            'phone': ['0241234567', '0551234567'],
            'address': ['123 Main St, Accra', '456 Oak Ave, Kumasi'],
            'ghana_card_number': ['GHA-123456789-0', 'GHA-987654321-1'],
            'qualification': ['bachelor', 'master'],
            'specialization': ['Mathematics', 'English Language'],
            'employment_status': ['permanent', 'contract'],
            'hire_date': ['2020-09-01', '2021-01-15'],
        }
        
        df = pd.DataFrame(data)
        return df
