from django.db import models
from core.models import Person


class Teacher(Person):
    """Teacher model extending the Person abstract model"""
    
    EMPLOYMENT_STATUS = (
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('temporary', 'Temporary'),
    )
    
    QUALIFICATION_CHOICES = (
        ('diploma', 'Diploma'),
        ('bachelor', 'Bachelor\'s Degree'),
        ('master', 'Master\'s Degree'),
        ('phd', 'PhD'),
    )
    
    employee_id = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False
    )
    
    qualification = models.CharField(
        max_length=20, 
        choices=QUALIFICATION_CHOICES
    )
    
    specialization = models.CharField(
        max_length=100,
        help_text="Subject or area of specialization"
    )
    
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS,
        default='permanent'
    )
    
    hire_date = models.DateField()
    
    profile_picture = models.ImageField(
        upload_to='teachers/profiles/',
        blank=True,
        null=True
    )
    
    class Meta:
        db_table = 'teachers_teacher'
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
        ordering = ['-created_at']
    
    @property
    def full_name(self):
        """Alias for get_full_name() to match User model expectation"""
        return self.get_full_name()
    
    def save(self, *args, **kwargs):
        # Generate employee_id if not exists
        if not self.employee_id:
            self.employee_id = self.generate_employee_id()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_employee_id():
        """Generate unique employee ID"""
        prefix = "TCH"
        # Get the last teacher's ID
        last_teacher = Teacher.objects.order_by('-id').first()
        if last_teacher and last_teacher.employee_id:
            try:
                last_number = int(last_teacher.employee_id[3:])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:05d}"
    
    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()}"
