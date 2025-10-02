from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from teachers.models import Teacher, Subject, TeacherSubject
import random
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample teachers with auto-generated passwords'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of sample teachers to create'
        )
        parser.add_argument(
            '--with-portal',
            action='store_true',
            help='Create portal access for all sample teachers'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        with_portal = options['with_portal']
        
        # Sample data
        first_names = [
            'John', 'Mary', 'James', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
            'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
            'Thomas', 'Sarah', 'Christopher', 'Karen', 'Charles', 'Nancy', 'Daniel', 'Lisa',
            'Matthew', 'Betty', 'Anthony', 'Helen', 'Mark', 'Sandra'
        ]
        
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
            'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson'
        ]
        
        qualifications = ['diploma', 'bachelor', 'master', 'phd', 'certificate']
        employment_statuses = ['full_time', 'part_time', 'contract']
        specializations = [
            'Mathematics', 'English Language', 'Science', 'Social Studies', 'Physical Education',
            'Art', 'Music', 'Computer Science', 'History', 'Geography', 'Biology', 'Chemistry',
            'Physics', 'Literature', 'French', 'Spanish', 'Religious Studies', 'Economics'
        ]
        
        # Ensure we have some subjects
        subjects_data = [
            {'name': 'Mathematics', 'code': 'MATH'},
            {'name': 'English Language', 'code': 'ENG'},
            {'name': 'Science', 'code': 'SCI'},
            {'name': 'Social Studies', 'code': 'SOC'},
            {'name': 'Information Technology', 'code': 'ICT'},
            {'name': 'Physical Education', 'code': 'PE'},
            {'name': 'Art', 'code': 'ART'},
            {'name': 'Music', 'code': 'MUS'},
        ]
        
        # Create subjects if they don't exist
        created_subjects = []
        for subject_data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                code=subject_data['code'],
                defaults={'name': subject_data['name']}
            )
            created_subjects.append(subject)
        
        self.stdout.write(
            self.style.SUCCESS(f'Ensured {len(created_subjects)} subjects exist.')
        )
        
        # Create teachers
        created_teachers = []
        passwords_info = []
        
        for i in range(count):
            # Generate teacher data
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}@schoolsystem.edu"
            
            # Make sure email is unique
            counter = 1
            original_email = email
            while User.objects.filter(email=email).exists():
                email = f"{first_name.lower()}.{last_name.lower()}{counter}@schoolsystem.edu"
                counter += 1
            
            # Create teacher
            teacher_data = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'gender': random.choice(['M', 'F']),
                'date_of_birth': date(
                    random.randint(1970, 1995),
                    random.randint(1, 12),
                    random.randint(1, 28)
                ),
                'phone': f"+233{random.randint(200000000, 599999999)}",
                'address': f"{random.randint(1, 999)} {random.choice(['Main St', 'Oak Ave', 'Park Rd', 'Church St'])}, Kumasi",
                'employee_id': f"EMP{1000 + i:03d}",
                'qualification': random.choice(qualifications),
                'specialization': random.choice(specializations),
                'experience_years': random.randint(1, 25),
                'employment_status': random.choice(employment_statuses),
                'date_hired': timezone.now().date() - timedelta(days=random.randint(30, 3650)),
                'salary': random.randint(2000, 8000) if random.choice([True, False]) else None,
            }
            
            teacher = Teacher.objects.create(**teacher_data)
            created_teachers.append(teacher)
            
            # Create portal access if requested
            if with_portal:
                user, generated_password = User.objects.create_user_with_generated_password(
                    email=email,
                    user_type='teacher',
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    is_active_portal=True
                )
                teacher.user = user
                teacher.save()
                
                passwords_info.append({
                    'name': teacher.get_full_name(),
                    'email': email,
                    'password': generated_password
                })
            
            # Assign random subjects
            num_subjects = random.randint(1, 3)
            assigned_subjects = random.sample(created_subjects, num_subjects)
            
            for j, subject in enumerate(assigned_subjects):
                TeacherSubject.objects.create(
                    teacher=teacher,
                    subject=subject,
                    is_primary=(j == 0)  # First subject is primary
                )
            
            self.stdout.write(f'Created teacher: {teacher.get_full_name()}')
        
        # Display results
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {len(created_teachers)} teachers!')
        )
        
        if with_portal:
            self.stdout.write(
                self.style.WARNING('\n' + '='*60)
            )
            self.stdout.write(
                self.style.WARNING('GENERATED PASSWORDS (SAVE THESE SECURELY):')
            )
            self.stdout.write(
                self.style.WARNING('='*60)
            )
            
            for info in passwords_info:
                self.stdout.write(f"Name: {info['name']}")
                self.stdout.write(f"Email: {info['email']}")
                self.stdout.write(f"Password: {info['password']}")
                self.stdout.write('-' * 40)
            
            self.stdout.write(
                self.style.WARNING('\nPlease save these passwords securely!')
            )
            self.stdout.write(
                self.style.SUCCESS('\nTip: You can also view/reset passwords from the teacher detail pages in the web interface.'))
        
        self.stdout.write(
            self.style.SUCCESS(f'\nAll teachers created successfully!')
        )
        
        # Provide helpful next steps
        self.stdout.write('\n' + '='*60)
        self.stdout.write('NEXT STEPS:')
        self.stdout.write('='*60)
        self.stdout.write('1. Visit http://localhost:8000/teachers/ to view all teachers')
        self.stdout.write('2. Click on any teacher to view/manage their portal access')
        self.stdout.write('3. Use "Reset Password" to generate new credentials anytime')
        if with_portal:
            self.stdout.write('4. Use "Send Credentials" button to share login details (email/SMS coming soon)')
        self.stdout.write('='*60)