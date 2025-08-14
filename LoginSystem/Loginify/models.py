from django.db import models
from django.utils import timezone
import os

# Create your models here.

def user_profile_picture_path(instance, filename):
    """
    Generate upload path for user profile pictures
    Path: media/profile_pictures/username/filename
    """
    # Get file extension
    ext = filename.split('.')[-1]
    # Create new filename: username.extension
    filename = f"{instance.username}.{ext}"
    return os.path.join('profile_pictures', instance.username, filename)

class UserDetails(models.Model):
    #UserDetails model for storing user registration info
    
    username = models.CharField(max_length=50, primary_key=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=12, blank=True)
    profile_picture = models.ImageField(
        upload_to=user_profile_picture_path,
        blank=True,
        null=True,
        help_text="Upload a profile picture (JPG, PNG, GIF supported)",
        verbose_name="Profile Picture"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.username
    
    def get_profile_picture_url(self):
        """
        Return profile picture URL or default avatar
        """
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return '/static/images/default-avatar.png'  # Default avatar path
    
    def delete_old_profile_picture(self):
        """
        Delete old profile picture file when updating
        """
        if self.profile_picture:
            try:
                if os.path.isfile(self.profile_picture.path):
                    os.remove(self.profile_picture.path)
            except:
                pass
    
    class Meta:
        verbose_name = "User Detail"
        verbose_name_plural = "User Details"
