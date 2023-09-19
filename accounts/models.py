from django.db import models 
import re
from django.core.exceptions import ValidationError


from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from phone_field import PhoneField
from .manager import CustomUserManager

import random
import string
import time

from django.conf import settings
# Create your models here.


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email_address'), unique=True)
    phone = PhoneField(help_text='Contact phone number', unique=True)
    is_blocked = models.BooleanField(default=False)
    referral_code = models.CharField(default='', unique=True, max_length=20)
    refered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    is_referred = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            unique_code = self._generate_unique_code()
            self.referral_code = unique_code
        super().save(*args, **kwargs)
            
            
    def _generate_unique_code(self):
        characters = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choice(characters) for _ in range(6))
            code+=str(int(time.time()))
            if not CustomUser.objects.filter(referral_code=code).exists():
                return code
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    
    objects = CustomUserManager()
    
    
def validate_phone_number(value):
    phone_number_regex = re.compile(r"^(?:\+?91[\-\s]?)?[789]\d{9}$")
    if not phone_number_regex.match(value):
        raise ValidationError('Invalid phone number format')
 
 
class Country(models.Model):
    name = models.CharField(max_length=80) 
    
    def __str__(self):
        return self.name
    
 
class State(models.Model):
    name = models.CharField(max_length=50)
    country = models.ForeignKey(Country, on_delete = models.CASCADE)    

    def __str__(self):
        return self.name
 
    
class Address(models.Model):
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField(_('email_address'), unique=True)
    phoneNumber = models.CharField(validators = [validate_phone_number], unique = True)
    addressline1 = models.CharField(max_length=255)
    addressline2 = models.CharField(max_length=255)
    city = models.CharField(max_length=80)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    pin = models.CharField(max_length=20)
    is_deleted = models.BooleanField(default=False)
    
    
    def __str__(self):
        return self.user.first_name
    
    
class Notifications(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField(default="default test message")
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return self.message
    
    

    
    
    
