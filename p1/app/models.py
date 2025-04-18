from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
import uuid

class CustomUser(AbstractUser):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+91'. Up to 12 digits allowed."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=False, unique=True)
    email = models.EmailField(unique=True)
    client_id = models.CharField(max_length=36, null=True, blank=True)

    def __str__(self):
        return self.email




