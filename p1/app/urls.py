from django.urls import path
from . import views

urlpatterns = [
    path('', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('forget/', views.ForgotPasswordView.as_view(), name='forget'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
]