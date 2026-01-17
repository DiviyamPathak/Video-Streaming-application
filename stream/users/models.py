from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(AbstractUser):
    # Basic fields needed for a streaming platform
    bio = models.TextField(blank=True, null=True)
    is_streamer = models.BooleanField(default=False)

    def __str__(self):
        return self.username
