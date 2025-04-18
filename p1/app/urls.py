from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('auth/', views.login, name='login_or_signup_user'),
    path('logout/', views.logout_user, name='logout'),
    path('forgot-password/', views.forgot_password, name='forget'),
    path('change-password/', views.change_password, name='change_password'),
]