from django.db import models

# Create your models here.

class UserDetails(models.Model):
    #UserDetails model for storing user registration info
    
    username = models.CharField(max_length=50, primary_key=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=12, blank=True)
    
    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name = "User Detail"
        verbose_name_plural = "User Details"
