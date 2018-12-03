from django.db import models

from patients.models import Patient

def user_directory_path_orignal(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'brain_tumour/{0}/orignal/{1}'.format(instance.patient.username, filename)

def user_directory_path_clustered(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'brain_tumour/{0}/clustered/{1}'.format(instance.patient.username, filename)

# Create your models here.
class BrainTumour(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='brain_tumour')
    timestamp = models.DateTimeField(auto_now_add=True)
    uploaded = models.FileField(upload_to=user_directory_path_orignal)
    clustered = models.FileField(upload_to=user_directory_path_clustered, blank=True)
    stage = models.CharField(max_length=7, blank=True)

    def __str__(self):
        return self.patient.username + 'brain_tumour'


    
