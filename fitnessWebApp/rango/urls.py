from django.urls import path
from rango import views

app_name = 'rango'

urlpatterns = [
    path('', views.about, name='about'),
    path('loggedIn/', views.homePage, name='homePage'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('exercises/', views.exercises, name='exercises'),
    path('exercises/autocomplete/', views.auto_complete_function, name='auto_complete_function'),
    path('exercises/activity_process/', views.activity_process, name='activity_process'),
    path('exercises/filter_activities/', views.filter_activities, name='filter_activities'),
    path('calories/', views.calories, name='calories'),
    path('calories/create/', views.meal_process, name='meal_process'),
    path('report/', views.report, name='report'),    
]