# views/utils.py

import re
import random
import time
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

User = get_user_model()
OTP_VALID_SECONDS = 600

def is_valid_email(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)

def is_valid_name(name):
    return bool(re.fullmatch(r'[A-Za-z]{1,30}', name))

def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[^A-Za-z0-9]', password):
        return False
    return True

def generate_otp():
    return str(random.randint(100000, 999999))

def is_otp_expired(created_at):
    return (time.time() - float(created_at)) > OTP_VALID_SECONDS


def send_otp_email(email, otp):
    return send_mail(
        'Your OTP for Password Reset',
        f'Your OTP is: {otp}\nThis OTP is valid for 10 minutes.',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

def get_user_by_email(email):
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None

def create_unique_username(email):
    base_username = email.split('@')[0][:30]
    username = base_username
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{random.randint(1, 9)}"
    return username

def create_new_user(username, email, phone, password, first_name, last_name):
    user = User.objects.create_user(
        username=username,
        email=email,
        phone=phone,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    return user
