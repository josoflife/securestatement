from django.urls import path
from . import views

urlpatterns = [
    path('', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('statements/download/<str:token>/', views.download_statement, name='download_statement'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('generate/', views.generate_statement, name='generate_statement'),

]
