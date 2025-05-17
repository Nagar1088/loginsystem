from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.views.decorators.cache import never_cache

import re, time, random

from .models import CustomUser

User = get_user_model()
OTP_VALID_SECONDS = 120


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html', {'active_tab': 'login'})

    def post(self, request):
        print("Login form data received:", request.POST)
        email = request.POST.get('email', '').strip()
        password = request.POST.get('pswd', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        if len(first_name) > 10:
            messages.error(request, 'First name must be less than 10 characters')
            return render(request, 'login.html', {'first_name': first_name, 'active_tab': 'login'})

        if len(last_name) > 15:
            messages.error(request, 'Last name must be less than 15 characters')
            return render(request, 'login.html', {'last_name': last_name, 'active_tab': 'login'})

        if not email or not password:
            messages.error(request, 'Please enter both email and password')
            return render(request, 'login.html', {'email': email, 'active_tab': 'login'})

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messages.error(request, 'Please enter a valid email address')
            return render(request, 'login.html', {'email': email, 'active_tab': 'login'})

        if len(password) <= 8:
            messages.error(request, 'Password must be at least 8 characters')
            return render(request, 'login.html', {'email': email, 'active_tab': 'login'})

        try:
            user = User.objects.get(email=email)
            authenticated_user = authenticate(request, username=user.username, password=password)
            if authenticated_user is not None:
                auth_login(request, authenticated_user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid password')
        except User.DoesNotExist:
            messages.error(request, 'Email not found')

        return render(request, 'login.html', {'email': email, 'active_tab': 'login'})

@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self, request):
        return render(request, 'dashboard.html')

class SignupView(View):
    def get(self, request):
        return render(request, 'login.html', {'active_tab': 'signup'})

    def post(self, request):
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
                'email': email, 'phone': phone, 'first_name': first_name, 'last_name': last_name, 'active_tab': 'signup'
            })

        errors = {}
        if not re.match(r'^[A-Za-z ]+$', first_name):
            errors['first_name'] = 'Please enter valid first name (only letters)'
        if not re.match(r'^[A-Za-z ]+$', last_name):
            errors['last_name'] = 'Please enter valid last name (only letters)'
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors['email'] = 'Invalid email address'
        if len(password) < 8:
            errors['password'] = 'Password too short'
        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'
        if CustomUser.objects.filter(email=email).exists():
            errors['email'] = 'Email already exists'
        if CustomUser.objects.filter(phone=phone).exists():
            errors['phone'] = 'Phone number already exists'

        if errors:
            for err in errors.values():
                messages.error(request, err)
            return render(request, 'login.html', {
                'email': email, 'phone': phone, 'first_name': first_name, 'last_name': last_name, 'active_tab': 'signup'
            })

        username = email.split('@')[0][:30]
        while CustomUser.objects.filter(username=username).exists():
            username = f"{username}{random.randint(1, 9)}"

        try:
            user = CustomUser.objects.create_user(username=username, email=email, phone=phone,
                                                  password=password, first_name=first_name, last_name=last_name)
            auth_login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('change_password')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'login.html', {
                'email': email, 'phone': phone, 'first_name': first_name, 'last_name': last_name, 'active_tab': 'signup'
            })


@method_decorator(never_cache, name='dispatch')
@method_decorator(login_required, name='dispatch')
class LogoutView(View):
    def get(self, request):
        logout(request)
        request.session.flush()
        response = redirect('login')
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response


class ForgotPasswordView(View):
    def get(self, request):
        step = request.session.get('step', 'send_otp')
        return render(request, 'forget.html', {'step': step})

    def post(self, request):
        step = request.session.get('step', 'send_otp')
        email = request.session.get('email')

        if 'send_otp' in request.POST:
            email_input = request.POST.get('email', '').strip()
            try:
                user = User.objects.get(email=email_input)
                otp = str(random.randint(100000, 999999))
                request.session.update({
                    'otp': otp,
                    'otp_email': email_input,
                    'otp_created_at': str(time.time()),
                    'step': 'verify_otp',
                    'email': email_input
                })
                send_mail(
                    'Your OTP for Password Reset',
                    f'Your OTP is: {otp}\nThis OTP is valid for 2 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email_input],
                    fail_silently=False,
                )
                messages.success(request, 'OTP sent to your email.')
                return redirect('forget')
            except User.DoesNotExist:
                messages.error(request, 'No user with this email.')
                return redirect('forget')

        elif 'resend_otp' in request.POST:
            if not email:
                messages.error(request, 'Session expired. Please enter your email again.')
                request.session['step'] = 'send_otp'
                return redirect('forget')
            try:
                user = User.objects.get(email=email)
                otp = str(random.randint(100000, 999999))
                request.session.update({
                    'otp': otp,
                    'otp_created_at': str(time.time()),
                    'step': 'verify_otp'
                })
                send_mail(
                    'Your OTP for Password Reset (Resent)',
                    f'Your new OTP is: {otp}\nThis OTP is valid for 2 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'New OTP sent to your email.')
                return redirect('forget')
            except User.DoesNotExist:
                messages.error(request, 'No user with this email.')
                request.session['step'] = 'send_otp'
                return redirect('forget')

        elif 'verify_otp' in request.POST:
            otp_input = request.POST.get('otp', '').strip()
            stored_otp = request.session.get('otp')
            otp_created_at = float(request.session.get('otp_created_at', 0))
            if (time.time() - otp_created_at) > OTP_VALID_SECONDS:
                messages.error(request, 'OTP expired. Request a new one.')
                request.session['step'] = 'send_otp'
                return redirect('forget')
            if otp_input == stored_otp:
                request.session['step'] = 'reset_password'
                messages.success(request, 'OTP verified. Now reset your password.')
                return redirect('forget')
            else:
                messages.error(request, 'Invalid OTP.')
                return redirect('forget')

        elif 'reset_password' in request.POST:
            password = request.POST.get('password', '').strip()
            confirm = request.POST.get('confirm', '').strip()
            has_error = False
            if password != confirm:
                messages.error(request, 'Passwords do not match.')
                has_error = True
            if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
                has_error = True
            if has_error:
                request.session['step'] = 'reset_password'
                return redirect('forget')
            try:
                user = User.objects.get(email=email)
                user.password = make_password(password)
                user.save()
                request.session.flush()
                messages.success(request, 'Password reset successfully.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'Something went wrong. Try again.')
                request.session.flush()
                return redirect('forget')

        return render(request, 'forget.html', {'step': step})


@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class ChangePasswordView(View):
    def get(self, request):
        response = render(request, 'change_password.html')
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def post(self, request):
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect')
            return redirect('change_password')
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match')
            return redirect('change_password')
        if len(new_password) < 8:
            messages.error(request, 'Password too short')
            return redirect('change_password')

        try:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

        return redirect('change_password')
