from django.contrib import admin
from .models import School, Domain


class SchoolAdminSite(admin.AdminSite):
    site_header = "School Management Admin"
    site_title = "School Management Portal"
    index_title = "Welcome to the School Management Admin Area"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register(School)
        self.register(Domain)

school_admin_site = SchoolAdminSite(name='school_admin')