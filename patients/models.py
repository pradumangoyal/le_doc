from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Patient(models.Model):
    GENDER_OPTIONS = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Not Disclosed'),
    )
    created = models.DateTimeField(auto_now_add=True)
    doctor  = models.ForeignKey(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=31, unique=True)
    name = models.CharField(max_length=63)
    age = models.CharField(max_length=7)
    gender = models.CharField(max_length=1, choices=GENDER_OPTIONS, default='N')
    contact = models.CharField(max_length=15)
    blood_group = models.CharField(max_length=3)

    def __str__(self):
        return self.username
    