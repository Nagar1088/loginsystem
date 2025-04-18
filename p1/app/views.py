from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import CustomUser
import re
import random, time
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.views.decorators.cache import never_cache

OTP_VALID_SECONDS = 600



from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, get_user_model
from django.contrib import messages
from django.views.decorators.cache import never_cache
import re
import random
from .models import CustomUser

@never_cache
def login(request):
    if request.method == 'POST':
        print("Login form data received:", request.POST)
        email = request.POST.get('email', '').strip()
        password = request.POST.get('pswd', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        if len(first_name) > 10:
            messages.error(request, 'First name must be less than 10 characters long')
            return render(request, 'login.html', {
                'first_name': first_name,
                'active_tab': 'login',
            })

        if len(last_name) > 15:
            messages.error(request, 'Last name must be less than 15 characters long')
            return render(request, 'login.html', {
                'last_name': last_name,
                'active_tab': 'login',
            })

        if not email or not password:
            messages.error(request, 'Please enter both email and password')
            return render(request, 'login.html', {
                'email': email,
                'active_tab': 'login',
            })

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messages.error(request, 'Please enter a valid email address')
            return render(request, 'login.html', {
                'email': email,
                'active_tab': 'login',
            })

        if len(password) <= 8:
            messages.error(request, 'Password must be at least 8 characters long')
            return render(request, 'login.html', {
                'email': email,
                'active_tab': 'login',
            })

        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            authenticated_user = authenticate(
                request,
                username=user.username,
                password=password
            )
            if authenticated_user is not None:
                auth_login(request, authenticated_user)
                return redirect('change_password')
            else:
                messages.error(request, 'Invalid password')
        except User.DoesNotExist:
            messages.error(request, 'Email not found')

        return render(request, 'login.html', {
            'email': email,
            'active_tab': 'login',
        })

    return render(request, 'login.html', {'active_tab': 'login'})

@never_cache
def signup(request):
    if request.method == 'POST':
        print("Signup form data received:", request.POST)
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('pswd', '').strip()
        confirm_password = request.POST.get('confirm_pswd', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        if not all([email, phone, password, confirm_password]):
            messages.error(request, 'Please fill all required fields')
            return render(request, 'login.html', {
                'email': email,
                'phone': phone,
                'first_name': first_name,
                'last_name': last_name,
                'active_tab': 'signup',
            })

        errors = {}
        if not re.match(r'[a-zA-Z]', first_name):
            errors['first_name'] = 'Please enter valid first_name'
        if not re.match(r'[a-zA-Z]', last_name):
            errors['last_name'] = 'Please enter valid last_name'
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors['email'] = 'Please enter a valid email address'
        if len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters long'
        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'
        if first_name and (len(first_name) > 30 or not first_name.isalpha()):
            errors['first_name'] = 'First name must contain only letters and be less than 30 characters'
        if last_name and (len(last_name) > 30 or not last_name.isalpha()):
            errors['last_name'] = 'Last name must contain only letters and be less than 30 characters'
        if CustomUser.objects.filter(email=email).exists():
            errors['email'] = 'Email already exists'
        if CustomUser.objects.filter(phone=phone).exists():
            errors['phone'] = 'Phone number already exists'

        if errors:
            for error in errors.values():
                messages.error(request, error)
            return render(request, 'login.html', {
                'email': email,
                'phone': phone,
                'first_name': first_name,
                'last_name': last_name,
                'active_tab': 'signup',
            })

        try:
            username = email.split('@')[0][:30]
            while CustomUser.objects.filter(username=username).exists():
                username = f"{username}{random.randint(1, 9)}"

            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                phone=phone,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            auth_login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('change_password')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'login.html', {
                'email': email,
                'phone': phone,
                'first_name': first_name,
                'last_name': last_name,
                'active_tab': 'signup',
            })

    return render(request, 'login.html', {'active_tab': 'signup'})


@never_cache
@login_required
def logout_user(request):
    logout(request)
    return redirect('login')



User = get_user_model()
otp_data = {}
@never_cache
def forgot_password(request):
    step = request.session.get('step', 'send_otp')
    email = request.session.get('email')
    if request.method == 'POST':
        if 'send_otp' in request.POST:
            email_input = request.POST.get('email').strip()
            try:
                user = User.objects.get(email=email_input)
                otp = str(random.randint(100000, 999999))
                request.session['otp'] = otp
                request.session['otp_email'] = email_input
                request.session['otp_created_at'] = str(time.time())
                try:
                    send_mail(
                        'Your OTP for Password Reset',
                        f'Your OTP is: {otp}\nThis OTP is valid for 10 minutes.',
                        settings.DEFAULT_FROM_EMAIL,
                        [email_input],
                        fail_silently=False,
                    )
                    request.session['email'] = email_input
                    request.session['step'] = 'verify_otp'
                    messages.success(request, 'OTP sent to your email.')
                    return redirect('forget')
                except Exception as e:
                    messages.error(request, f'Failed to send email: {str(e)}')
                    return redirect('forget')
            except User.DoesNotExist:
                messages.error(request, 'No user with this email.')
                return redirect('forget')
        elif 'verify_otp' in request.POST:
            otp_input = request.POST.get('otp').strip()
            stored_otp = request.session.get('otp')
            otp_created_at = float(request.session.get('otp_created_at', 0))
            if (time.time() - otp_created_at) > OTP_VALID_SECONDS:
                messages.error(request, 'OTP has expired. Please request a new one.')
                request.session['step'] = 'send_otp'
                return redirect('forget')
            if stored_otp and otp_input == stored_otp:
                request.session['step'] = 'reset_password'
                messages.success(request, 'OTP verified. Now reset your password.')
                return redirect('forget')
            else:
                messages.error(request, 'Invalid OTP.')
                return redirect('forget')
        elif 'reset_password' in request.POST:
            password = request.POST.get('password')
            confirm = request.POST.get('confirm')
            if password != confirm:
                messages.error(request, 'Passwords do not match.')
            elif len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
            else:
                user = User.objects.get(email=email)
                user.password = make_password(password)
                user.save()
                request.session.flush()
                messages.success(request, 'Password reset successfully.')
                return redirect('login')
    return render(request, 'forget.html', {
        'step': step,
    })


@never_cache
@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not request.user.check_password(old_password):
            messages.error(request, 'Your current password is incorrect')
            return redirect('change_password')
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match')
            return redirect('change_password')
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return redirect('change_password')
        try:
            request.user.set_password(new_password)
            request.user.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully!')
            return redirect('change_password')
        except Exception as e:
            messages.error(request, f'Error changing password: {str(e)}')
            return redirect('change_password')
    return render(request, 'change_password.html')