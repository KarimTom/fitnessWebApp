from django.urls import path
from rango import views

app_name = 'rango'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.user_login, name='login'),
    path('category/<slug:category_name_slug>/', views.show_category, name='category'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('BMI/', views.weightHeightUpdate, name='BMI'),
    path('exercises/', views.exercises, name='exercises'),
    path('workout', views.workout, name='workout'),
    path('calories/', views.calories, name='calories'),
    path('processWeightHeight/', views.weightHeightUpdate, name='processWeightHeight'),
    path('add_category/', views.add_category, name='add_category'),
    path('user_category/<slug:category_name_slug>/', views.user_category, name='user_category'),
]