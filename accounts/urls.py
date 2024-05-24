from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name="register"),
    path('login/', views.login, name="login"),
    path('logout/', views.logout, name="logout"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('', views.dashboard, name="dashboard"),
    
    path('forgotpassword/', views.forgot_password, name="forgotpassword"),
    path('resetpassword/', views.reset_password, name="resetpassword"),
    
    path('resetpassword_validate/<uidb64>/<token>', views.resetpassword_validate, name="resetpassword_validate"),
    
    path('activate/<uidb64>/<token>', views.activate, name="activate"),
]
