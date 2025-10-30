from django.db import models
from colorfield.fields import ColorField


class Item(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class SchoolSettings(models.Model):
    name = models.CharField(max_length=100)
    color = ColorField(default='#FFFFFF')
    logo = models.ImageField(upload_to='school_logos/', null=True, blank=True)

    def __str__(self):
        return self.name