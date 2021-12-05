from django.contrib.auth.models import User
from django.http.response import JsonResponse
from django.views import View
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rango.models import Activities, ActivityCategory, Food, Profile_food, Profile_activity, PostFood, UserProfile, Category, Video, PostActivities
from rango.forms import ChosenVideoForm, UserForm, UserProfileForm, ProfileForm, CategoryForm, VideoForm, SelectExerciseForm, SelectExerciseSearchForm
from django.utils import timezone
from datetime import date, datetime, timedelta
from django.db import connections
import json
import requests
import random
import tensorflow.compat.v1 as tf
import numpy as np
from keras import backend as K
from keras.applications import vgg16
from keras.applications.imagenet_utils import decode_predictions
from keras.preprocessing.image import img_to_array, load_img
from tensorflow.python.keras.backend import set_session
from django.views.decorators.csrf import csrf_exempt
from django.utils.datastructures import MultiValueDictKeyError

url_food_database = "https://api.edamam.com/api/food-database/v2/parser"
headers_food_database = {
    'app_id': "3ac2ff31",
    'app_key': "1726dd8e46e8e8027369ba1fc0054a41"
}

url_nutrition_analysis = "https://api.edamam.com/api/nutrition-data"
headers_nutrition_analysis = {
    'app_id': "c5cfcfef",
    'app_key': "9185b3aa75ac918cab425d8adc84e9a9"
}


def about(request):
    logout(request)
    return render(request, 'rango/about.html')

def index(request):
    print('index')
    context_dict = {}
    
    #all_videos = Video.objects.all()
    
    # if all_videos:
    #     for video in all_videos:
    #         print(video.title + " , " + str(video.id))
    if request.user.is_authenticated:
        loggedInUser_food = Profile_food.objects.filter(person=request.user).last()
        loggedInuser_activity = Profile_activity.objects.filter(person=request.user).last()
        print(loggedInUser_food)
        print(loggedInuser_activity)
        calories = loggedInUser_food.calorie_goal

        if date.today() != loggedInUser_food.date_today:
            print("Date is different -> Creating new Profile for this date")
            newProfile = Profile_food.objects.create(
                person=request.user, calorie_goal=calories)
            newProfile.save()
            newProfile = Profile_activity.objects.create(
                person=request.user
            )
            newProfile.save()

        loggedInUser_food = Profile_food.objects.filter(person=request.user).last()
        loggedInuser_activity = Profile_activity.objects.filter(person=request.user).last()
        calories_consumed = loggedInUser_food.calorie_consumed_day
        calorie_goal = loggedInUser_food.calorie_goal
                
        nutrients = Profile_food.objects.filter(person=request.user) \
            .values('protein_consumed_day', 'carbs_consumed_day', 'fats_consumed_day') \
            .last()

        nutrients_dict = [   
                            {'name': 'protein', 'value': nutrients['protein_consumed_day']},
                            {'name': 'carbs', 'value': nutrients['carbs_consumed_day']},
                            {'name': 'fats', 'value': nutrients['fats_consumed_day']}
                        ]
        nutrients_json = json.dumps(nutrients_dict)
        
        calories_dict = [   
                            {'name': 'calorie goal', 'value': calorie_goal, 'filler': 'orange'},
                            {'name': 'calories consumed', 'value': calories_consumed, 'filler': 'green'}
                        ]
        calories_json = json.dumps(calories_dict)

        li_activities = []
        activities = PostActivities.objects.all() \
            .values('description', 'calorie_amount', 'calorie_unit', 'time_min')

        for each_activity in activities:
            dict = {'name': each_activity['description'], 'calorie_burned': int(each_activity['calorie_amount']),
                    'unit': each_activity['calorie_unit'], 'duration': each_activity['time_min']}
            li_activities.append(dict)
        activities_json = json.dumps(li_activities)

        # if calories != 0:
        all_food = PostFood.objects.filter(profile=loggedInUser_food)
        context_dict['all_food_today_info'] = all_food
        context_dict['nutrients_info'] = nutrients_json
        context_dict['calories_info'] = calories_json
        context_dict['activities_info'] = activities_json
        
        print('index')
    return render(request, 'rango/index.html', context=context_dict)


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                print(request.user.userprofile.weight)
                print(request.user.userprofile.height)
                print(request.user.userprofile.BMI)
                return redirect(reverse('rango:index'))
            else:
                return HttpResponse("Your Rango account is disabled.")
        else:
            print(f"Invalid login details: {username}, {password}")
            return HttpResponse("Invalid login details supplied.")

    else:
        return render(request, 'rango/login.html')


def user_logout(request):
    logout(request)
    return redirect(reverse('rango:about'))


def register(request):
    registered = False
    context_dict = {}
    
    if request.method == 'POST':
        print(request.POST)
        user_form = UserForm(request.POST)
        user_profile_form = UserProfileForm(request.POST)
        profile_form = ProfileForm(request.POST)

        if user_form.is_valid() and user_profile_form.is_valid() and profile_form.is_valid():
            print("Everything is valid -> saving...")

            if request.POST['gender'] == 'male':
                BMR = int(88.362 + 
                         (13.397 * float(request.POST['weight'])) + 
                         (4.799 * float(request.POST['height'])) - 
                         (5.677 * float(request.POST['age']))
                         )
            else:
                BMR = int(447.593 + 
                         (9.247 * float(request.POST['weight'])) + 
                         (3.098 * float(request.POST['height'])) - 
                         (4.330 * float(request.POST['age']))
                         )

            user = user_form.save()
            user.set_password(user.password)
            user.save()

            userProfile = user_profile_form.save(commit=False)
            userProfile.user = user
            userProfile.BMR = BMR
            userProfile.save()

            profile_food = profile_form.save(commit=False)
            profile_food.person = user
            
            if request.POST['calorie_goal'] == '0' or request.POST['calorie_goal'] == '':
                print('we are here')
                if request.POST['goal'] == 'bulk':
                    cal_goal = BMR + (0.20 * BMR)
                elif request.POST['goal'] == 'maintenance':
                    cal_goal = BMR + (0.05 * BMR)
                else:
                    cal_goal = BMR - (0.10 * BMR)

                profile_food.calorie_goal = cal_goal
            profile_food.save()

            Profile_activity.objects.create(person=user)

            info_user_profile = UserProfile.objects.get(user=user)
            info_profile_food = Profile_food.objects.get(person=user)

            registered = True

            context_dict['BMR'] = BMR
            context_dict['age'] = info_user_profile.age
            context_dict['weight'] = info_user_profile.weight
            context_dict['height'] = info_user_profile.height
            context_dict['BMI'] = info_user_profile.BMI
            context_dict['calorie_goal'] = info_profile_food.calorie_goal
        else:
            print(user_form.errors, profile_form.errors,
                  user_profile_form.errors)
    else:
        user_form = UserForm()
        user_profile_form = UserProfileForm()
        profile_form = ProfileForm()

    return render(request, 'rango/register.html', context={'user_form': user_form,
                                                           'profile_form': profile_form,
                                                           'user_profile_form': user_profile_form,
                                                           'registered': registered,
                                                           'info': context_dict})

def weightHeightUpdate(request):
    context_dict = {}
    form = UserProfileForm()

    if request.user.is_authenticated:
        print(request.user)
        loggedInUser = UserProfile.objects.filter(user=request.user).last()
        print(loggedInUser.user.userprofile.weight)
        context_dict['BMI'] = loggedInUser.user.userprofile.BMI
        if request.method == 'POST':
            form = UserProfileForm(request.POST, instance=loggedInUser)
            if form.is_valid:
                form.save()
                context_dict['BMI'] = loggedInUser.user.userprofile.BMI
    else:
        if request.method == 'POST':
            weight = float(request.POST.get('weight'))
            height = float(request.POST.get('height'))

            BMI = (weight / height) * 100
            context_dict['BMI'] = BMI

    return render(request, 'rango/BMI.html', context=context_dict)


def profile(request):
    context_dict = {}

    user_profile = UserProfile.objects.filter(user=request.user) \
        .values('age', 'weight', 'height', 'gender', 'goal', 'BMR', 'BMI') \
        .last()

    profile_food = Profile_food.objects.filter(person=request.user) \
        .values('calorie_goal') \
        .last()

    context_dict['gender'] = user_profile['gender']
    context_dict['BMR'] = user_profile['BMR']
    context_dict['BMI'] = user_profile['BMI']

    context_dict['age'] = user_profile['age']
    context_dict['weight'] = user_profile['weight']
    context_dict['height'] = user_profile['height']
    context_dict['goal'] = user_profile['goal'].upper()
    
    
    context_dict['calorie_goal'] = profile_food['calorie_goal']

    return render(request, 'rango/profile.html', context=context_dict)


def exercises(request):
    context_dict = {}

    category_list = Category.objects.all()
    context_dict['categories'] = category_list

    loggedInUser_activity = Profile_activity.objects.filter(person=request.user).last()
    if request.user.is_authenticated:
        video_add_form = VideoForm()
        activity_add_form = SelectExerciseForm()
        activity_search_add_form = SelectExerciseSearchForm()
        if request.method == 'POST':
            form = VideoForm(request.POST)
            if form.is_valid:
                saved_video = form.save()
                types = str(request.POST.get('categories'))
                list_of_categories = types.split(', ')
                video = Video.objects.get_or_create(title=saved_video)[0]
                for category in list_of_categories:
                    cat = Category.objects.get_or_create(name=category)[0]
                    print(str(cat.name) + " , " + str(cat.id))
                    cat.videos.add(video)

        context_dict['videoForm'] = video_add_form
        context_dict['ActivityForm'] = activity_add_form
        context_dict['ActivitySearchForm'] = activity_search_add_form

        li_activities = []
        activities = PostActivities.objects.filter(profile=loggedInUser_activity) \
            .values('description', 'calorie_amount', 'calorie_unit', 'time_min')

        for each_activity in activities:
            dict = {'name': each_activity['description'], 'calorie_burned': int(each_activity['calorie_amount']),
                    'unit': each_activity['calorie_unit'], 'duration': each_activity['time_min']}
            li_activities.append(dict)

        activities_json = json.dumps(li_activities)
        context_dict['activities_info'] = activities_json

    return render(request, 'rango/exercises.html', context=context_dict)


def show_category(request, category_name_slug):
    context_dict = {}
    form = ChosenVideoForm
    try:

        category = Category.objects.get(slug=category_name_slug)
        all_videos = category.videos.all()
        print(all_videos)
        context_dict['category'] = category
        context_dict['videos'] = all_videos
        context_dict['form'] = form
    except Category.DoesNotExist:
        context_dict['category'] = None
        context_dict['videos'] = None
        context_dict['form'] = None

    return render(request, 'rango/category.html', context=context_dict)

def workout(request):
    context_dict = {}

    loggedInUser = UserProfile.objects.get_or_create(user=request.user)[0]
    cats = Category.objects.all()

    if request.method == 'POST':
        user_video_add = Video.objects.get_or_create(
            id=request.POST.get('videoId'))[0]
        print(user_video_add.title)
        print(request.POST.get('videoId'))
        loggedInUser.video.add(user_video_add)

    all_videos = loggedInUser.video.all()
    print(all_videos)

    category_list = []
    for category in cats:
        print("checking category " + category.name)
        category_all_videos = category.videos.all()
        for category_video in category_all_videos:
            for user_video_added in all_videos:
                print(str(category_video.title) +
                      " , " + str(user_video_added.title))
                if category_video.title == user_video_added.title:
                    print("Validated")
                    category_list.append(category)

    context_dict['categories'] = category_list
    print(context_dict['categories'])

    return render(request, 'rango/workout.html', context=context_dict)


def user_category(request, category_name_slug):
    context_dict = {}

    loggedInUser = UserProfile.objects.get_or_create(user=request.user)[0]
    print(category_name_slug)
    category = Category.objects.get(slug=category_name_slug)
    vids_category = category.videos.all()  # videos of this category

    vids_user = loggedInUser.video.all()  # videos of the user

    # logged in user with videos in videos of this category
    vids_list = []
    for v_c in vids_category:
        for v_u in vids_user:
            if v_u.id == v_c.id:
                vids_list.append(v_u)

    context_dict['videos'] = vids_list
    context_dict['category'] = category
    return render(request, 'rango/user_category.html', context=context_dict)


@login_required
def add_category(request):
    form = CategoryForm()

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        print(request.POST)
        if form.is_valid():
            form.save(commit=True)
            return redirect(reverse('rango:index'))
        else:
            print(form.errors)
    return render(request, 'rango/add_category.html', {'form': form})

##import tensorflow as tf
##from keras.models import load_model
##from keras.preprocessing import image
##from tensorflow import Graph, Session
##import json


# img_height, img_width = 224, 224
# with open('./models/keras.json', 'r') as f:
#     labelInfo = f.read()

# labelInfo = json.loads(labelInfo)

# model_graph = Graph()
# with model_graph.as_default():
#     tf_session = Session() 
#     with tf_session.as_default():
#         model = load_model('./models/vgg16_weights_tf_dim_ordering_tf_kernels.h5')


def get_suggestion(calories, 
                   high_protein_flag, high_carb_flag, high_fat_flag,
                   max_protein_perc, max_carb_perc, max_fat_perc,
                   min_protein_perc, min_carb_perc, min_fat_perc):

    min_carb_percentage = min_carb_perc
    max_carb_percentage = max_carb_perc
    min_carb_gr = int(min_carb_percentage * calories / 4)
    max_carb_gr = int(max_carb_percentage * calories / 4)

    min_protein_percentage = min_protein_perc
    max_protein_percentage = max_protein_perc
    min_protein_gr = int(min_protein_percentage * calories / 4)
    max_protein_gr = int(max_protein_percentage * calories / 4)

    min_fat_percentage = min_fat_perc
    max_fat_percentage = max_fat_perc
    min_fat_gr = int(min_fat_percentage * calories / 9)
    max_fat_gr = int(max_fat_percentage * calories / 9)

    print("In function now")

    print("Max Protein Percentage: Max Carbs Percentage: Max Fat Percentage:")
    print(max_protein_percentage,max_carb_percentage,max_fat_percentage)

    print("New Protein Max percentage: New Carbs Max Percentage: New fat Max Percentage:")
    print(max_protein_percentage - high_protein_flag,max_carb_percentage - high_carb_flag,max_fat_percentage - high_fat_flag)

    if high_protein_flag != 0:

        if max_protein_percentage - high_protein_flag < 0:
            min_protein_gr = 3
            max_protein_gr = int(0.15 * calories / 4)
            min_protein_gr = min(min_protein_gr, max_protein_gr)
            max_protein_gr = max(min_protein_gr, max_protein_gr)
            protein_qtity = str(min_protein_gr) + "-" + str(max_protein_gr)
        elif max_protein_percentage - high_protein_flag < min_protein_percentage:
            min_protein_gr = 3
            protein_cal = (max_protein_percentage - high_protein_flag) * calories
            max_protein_gr = int(protein_cal / 4)
            min_protein_gr = min(min_protein_gr, max_protein_gr)
            max_protein_gr = max(min_protein_gr, max_protein_gr)
            protein_qtity = str(min_protein_gr) + "-" + str(max_protein_gr)
        else:
            protein_cal = (max_protein_percentage - high_protein_flag) * calories
            max_protein_gr = int(protein_cal / 4)
            protein_qtity = str(min_protein_gr) + "-" + str(max_protein_gr)
        
    else:
        protein_qtity = str(min_protein_gr) + "-" +str(max_protein_gr)

    if high_carb_flag != 0:

        if max_carb_percentage - high_carb_flag < 0:
            min_carb_gr = 3
            max_carb_gr = int(0.15 * calories / 4)
            min_carb_gr = min(min_carb_gr, max_carb_gr)
            max_carb_gr = max(min_carb_gr, max_carb_gr)
            carb_qtity = str(min_carb_gr) + "-" + str(max_carb_gr)
        elif max_carb_percentage - high_carb_flag < min_carb_percentage:
            min_carb_gr = 3
            carb_cal = (max_carb_percentage - high_carb_flag) * calories
            max_carb_gr = int(carb_cal / 4)
            min_carb_gr = min(min_carb_gr, max_carb_gr)
            max_carb_gr = max(min_carb_gr, max_carb_gr)
            carb_qtity = str(min_carb_gr) + "-" + str(max_carb_gr)
        else:
            carb_cal = (max_carb_percentage - high_carb_flag) * calories
            max_carb_gr = int(carb_cal / 4)
            carb_qtity = str(min_carb_gr) + "-" + str(max_carb_gr)

    else:
        carb_qtity = str(min_carb_gr) + "-" +str(max_carb_gr)
    
    if high_fat_flag != 0: 

        if max_fat_percentage - high_fat_flag < 0:
            min_fat_gr = 3
            max_fat_gr = int(0.15 * calories / 9)
            min_fat_gr = min(min_fat_gr, max_fat_gr)
            max_fat_gr = max(min_fat_gr, max_fat_gr)
            fat_qtity = str(min_fat_gr) + "-" + str(max_fat_gr)
        elif max_fat_percentage - high_fat_flag < min_fat_percentage:
            min_fat_gr = 3
            fat_cal = (max_fat_percentage - high_fat_flag) * calories
            max_fat_gr = int(fat_cal / 9)
            min_fat_gr = min(min_fat_gr, max_fat_gr)
            max_fat_gr = max(min_fat_gr, max_fat_gr)
            fat_qtity = str(min_fat_gr) + "-" + str(max_fat_gr)
        else:
            fat_cal = (max_fat_percentage - high_fat_flag) * calories
            max_fat_gr = int(fat_cal / 9)
            fat_qtity = str(min_fat_gr) + "-" + str(max_fat_gr)
    else:
        fat_qtity = str(min_fat_gr) + "-" +str(max_fat_gr)

    print('protein:' +protein_qtity)
    print('carbs:' +carb_qtity)
    print('fat:' +fat_qtity)

    try:
        querystring = {
                    "app_id": headers_food_database['app_id'],
                    "app_key": headers_food_database['app_key'],
                    "ingr": "..",
                    "category": ["generic-meals"],
                    "nutrients[CHOCDF]": carb_qtity,
                    "nutrients[PROCNT]": protein_qtity,
                    "nutrients[FAT]": fat_qtity
                    }
        
        
        response = requests.request(
                        "GET", url_food_database, params=querystring).json()

        print(response)

        n = random.sample(range(0, len(response['hints'])-1), 5)
        print(n)
    except ValueError:
        try:
            querystring = {
                        "app_id": headers_food_database['app_id'],
                        "app_key": headers_food_database['app_key'],
                        "ingr": "..",
                        "nutrients[CHOCDF]": carb_qtity,
                        "nutrients[PROCNT]": protein_qtity,
                        "nutrients[FAT]": fat_qtity
                        }
            
            
            response = requests.request(
                            "GET", url_food_database, params=querystring).json()

            print(response)

            n = random.sample(range(0, len(response['hints'])-1), 5)
            print(n)
        except ValueError:
            querystring = {
                        "app_id": headers_food_database['app_id'],
                        "app_key": headers_food_database['app_key'],
                        "ingr": "..",
                        "nutrients[CHOCDF]": str(0) + "-" + str(max_carb_gr),
                        "nutrients[PROCNT]": str(0) + "-" + str(max_protein_gr),
                        "nutrients[FAT]": str(0) + "-" + str(max_fat_gr)
                        }
            
            
            response = requests.request(
                            "GET", url_food_database, params=querystring).json()

            print(response)

            n = random.sample(range(0, len(response['hints'])-1), 5)
            print(n)

    food_list = []

    for i in n:
        print(response['hints'][i])
        print(
                 "Energy: " + str(int(response['hints'][i]['food']['nutrients']['ENERC_KCAL'])))
        print(
                 "Protein: " + str(int(response['hints'][i]['food']['nutrients']['PROCNT'])))
        print(
                 "Carbs: " + str(int(response['hints'][i]['food']['nutrients']['CHOCDF'])))
        print(
                 "Fat: " + str(int(response['hints'][i]['food']['nutrients']['FAT'])))
        print("\n")
        dict = {'name': response['hints'][i]['food']['label'],
                'Protein': int(response['hints'][i]['food']['nutrients']['PROCNT']),
                'Carbs': int(response['hints'][i]['food']['nutrients']['CHOCDF']),
                'Fat': int(response['hints'][i]['food']['nutrients']['FAT'])
                 }
        food_list.append(dict)

    return food_list

def calories(request):
    context_dict = {}
    context_dict['last_meal'] = None
    context_dict['food_sug'] = None
    context_dict['meals'] = None
    context_dict['predictions'] = None

    context_dict['high_protein_flag'] = context_dict['high_carb_flag'] = context_dict['high_fat_flag'] = None

    if request.user.is_authenticated:
        loggedInUser_food = Profile_food.objects.filter(person=request.user).last()
        print(loggedInUser_food.calorie_consumed_day)

        user_profile = UserProfile.objects.get(user=request.user)
        goal = user_profile.goal
    
        meals_taken = PostFood.objects.filter(profile=loggedInUser_food)
        print("meals taken for ", loggedInUser_food.person.username, meals_taken)
        last_meal = PostFood.objects.filter(profile=loggedInUser_food).last()
        
        print(last_meal)

        if last_meal:
            dict = {'name': last_meal.food.name,
                    'protein': last_meal.food.protein,
                    'carbs': last_meal.food.carbs,
                    'fat': last_meal.food.fat
                    }
            last_meal_json = json.dumps(dict)
            context_dict['last_meal'] = last_meal_json
            print(last_meal_json)

            calories = last_meal.food.calorie

            if goal == 'MAINTENANCE':
                max_protein_perc = 0.35
                min_protein_perc = 0.25

                max_carb_perc = 0.50
                min_carb_perc = 0.30

                max_fat_perc = 0.35
                min_fat_perc = 0.25

            elif goal == 'BULK':
                max_protein_perc = 0.35
                min_protein_perc = 0.25
                
                max_carb_perc = 0.60
                min_carb_perc = 0.40

                max_fat_perc = 0.25
                min_fat_perc = 0.15

            else:
                max_protein_perc = 0.50
                min_protein_perc = 0.40

                max_carb_perc = 0.30
                min_carb_perc = 0.10

                max_fat_perc = 0.40
                min_fat_perc = 0.30

            high_protein_flag = high_carb_flag = high_fat_flag = 0
            high_protein_flag = high_carb_flag = high_fat_flag = 0
            if last_meal.food.protein * 4 > max_protein_perc * calories:
                high_protein_flag = abs( max_protein_perc - ((last_meal.food.protein * 4)/calories) )
            if last_meal.food.carbs * 4>  max_carb_perc * calories:
                high_carb_flag = abs( max_carb_perc - ((last_meal.food.carbs * 4)/calories) )
            if last_meal.food.fat * 9> max_fat_perc * calories:
                high_fat_flag = abs( max_fat_perc - ((last_meal.food.fat * 9)/calories) )

            context_dict['high_protein_flag'] = high_protein_flag
            context_dict['high_carb_flag'] = high_carb_flag
            context_dict['high_fat_flag'] = high_fat_flag
            
            print("Last Meal Calories: Last Meal Protein: Last Meal Carbs: Last Meal Fat:")
            print(last_meal.food.calorie,last_meal.food.protein,last_meal.food.carbs,last_meal.food.fat)

            print("High Protein Flag, High Carb Flag, High Fat Flag:")
            print(high_protein_flag, high_carb_flag, high_fat_flag)

            print("Max Protein Perc: Max Carbs Perc: Max Fat Perc:")
            print(max_protein_perc, max_carb_perc, max_fat_perc)

            print("High Flag is the excess percentage with respect to max allowed percentage")

            list_sugg = get_suggestion(calories, 
                                       high_protein_flag, high_carb_flag, high_fat_flag,
                                       max_protein_perc, max_carb_perc, max_fat_perc,
                                       min_protein_perc, min_carb_perc, min_fat_perc)
            context_dict['food_sug'] = list_sugg

        dict_list = []
        for meal in meals_taken:
            dict =  { 'name': meal.food.name } \
                    ,{ 'protein': meal.food.protein } \
                    ,{ 'carbs': meal.food.carbs } \
                    ,{ 'fat': meal.food.fat } 
                    
            dict_list.append(dict)

        meals = json.dumps(dict_list)
        print(meals)
        context_dict['meals'] = meals                    

    file = None

    if request.method == "POST":  
        try:
            request.FILES["imageFile"]
            file = request.FILES["imageFile"]
            print(file.name)
            file_name = default_storage.save(file.name, file)
            file_url = default_storage.path(file_name)

            image = load_img(file_url, target_size=(224, 224))
            numpy_array = img_to_array(image)
            image_batch = np.expand_dims(numpy_array, axis=0)
            processed_image = vgg16.preprocess_input(image_batch.copy())

            ##with settings.GRAPH1.as_default():
            set_session(settings.SESS)
                ##settings.SESS.run(settings.init)
            predictions = settings.IMAGE_MODEL.predict(processed_image)
            print(predictions)
                
            labels = decode_predictions(predictions, top=5)

            for each_label in labels:
                for prediction in each_label:
                    type_predicted = prediction[1]
                    if '_' in type_predicted:
                        filter_string = str.split(type_predicted, '_')
                        print(filter_string)
                        type_predicted = ''
                        for strings in filter_string:
                            type_predicted += strings + ' '
                            print(type_predicted)
                    querystring = {"app_id": headers_nutrition_analysis['app_id'],
                                   "app_key": headers_nutrition_analysis['app_key'],
                                   "ingr": "100 gr " +type_predicted
                                   }
                    response = requests.request("GET", url_nutrition_analysis, params=querystring).json()
                    print(response)
                    if response['calories'] != 0:
                        print("type predicted is: " ,type_predicted)
                        print(response)
                        loggedInUser_food.meal = type_predicted
                        loggedInUser_food.save()
                        break
                    else:
                        context_dict['predictions'] = type_predicted
        except KeyError:
            print("Nothing was uploaded")
        # img = image.load_img(file_url, target_size=(img_height, img_width))
        # x = image.img_to_array(img)
        # x = x/255
        # x = x.reshape(1, img_height, img_width, 3)
        # with model_graph.as_default():
        #     with tf_session.as_default():
        #         predi = model.predict(x)

        # import numpy as np
        # predictedLabel = labelInfo[str(np.argmax(predi[0]))]
        # context_dict['predictions'] = predictedLabel

    return render(request, 'rango/calories.html', context=context_dict)

def activity_process(request):
    print(request.POST)
    loggedInUser_activity = Profile_activity.objects.filter(person=request.user).last()
    try:
        activity_selected = ActivityCategory.objects.get(id=request.POST['activity_category'])
        activity_overall= Activities.objects.get(activity_category=activity_selected, api_description=request.POST['Intensity_estimator'])
    except MultiValueDictKeyError:
        activity_overall = Activities.objects.get(api_description=request.POST['api_description'])

    time_in_min = request.POST['Time_in_min']
    description = request.POST['Description']

    loggedInUser_activity.activity = activity_overall
    loggedInUser_activity.time_min = int(float(time_in_min))
    loggedInUser_activity.description = description

    loggedInUser_activity.save()
    return redirect(reverse('rango:exercises'))
    
@csrf_exempt
def meal_process(request):
    # high carb food is more than 30 (normal is between 15 and 30) (study says 15-30 is high carb food)
    # high fat food is above 17.5 grams
    # high protein food is above 35 (normal is between 20 and 30)
    if request.is_ajax() and request.user.is_authenticated and request.method == 'POST':
        loggedInUser = Profile_food.objects.filter(person=request.user).last()

        user_profile = UserProfile.objects.get(user=request.user)
        goal = user_profile.goal
        print(goal)
        print('we are here')
        print(request.POST)
        meal = request.POST['name']
   
        profile = Profile_food.objects.filter(person=request.user).last()
        profile.meal = meal
        #profile.quantity = 'gr'
        profile.save()
        
        last_meal = PostFood.objects.filter(profile=loggedInUser).last()
        calories = last_meal.food.calorie

        if goal == 'maintenance':
            max_protein_perc = 0.35 
            min_protein_perc = 0.25

            max_carb_perc = 0.50 
            min_carb_perc = 0.30

            max_fat_perc = 0.35 
            min_fat_perc = 0.25
        elif goal == 'bulk':
            max_protein_perc = 0.35 
            min_protein_perc = 0.25

            max_carb_perc = 0.60 
            min_carb_perc = 0.40

            max_fat_perc = 0.25 
            min_fat_perc = 0.15
        else:
            max_protein_perc = 0.50 
            min_protein_perc = 0.40

            max_carb_perc = 0.30 
            min_carb_perc = 0.10

            max_fat_perc = 0.40  
            min_fat_perc = 0.30
        
        high_protein_flag = high_carb_flag = high_fat_flag = 0
        if last_meal.food.protein * 4 > max_protein_perc * calories:
            high_protein_flag = abs( max_protein_perc - ((last_meal.food.protein * 4)/calories) )
        if last_meal.food.carbs * 4 > max_protein_perc * calories:
            high_carb_flag = abs( max_carb_perc - ((last_meal.food.carbs * 4)/calories) )
        if last_meal.food.fat * 9> max_fat_perc * calories:
            high_fat_flag = abs( max_fat_perc - ((last_meal.food.fat * 9)/calories) )

        print("Last Meal Calories: Last Meal Protein: Last Meal Carbs: Last Meal Fat:")
        print(last_meal.food.calorie,last_meal.food.protein,last_meal.food.carbs,last_meal.food.fat)

        print("High Protein Flag, High Carb Flag, High Fat Flag:")
        print(high_protein_flag, high_carb_flag, high_fat_flag)

        print("Max Protein Perc: Max Carbs Perc: Max Fat Perc:")
        print(max_protein_perc, max_carb_perc, max_fat_perc)
            
        print("High Flag is the excess percentage with respect to max allowed percentage")

        list_sugg = get_suggestion(calories, 
                                   high_protein_flag, high_carb_flag, high_fat_flag,
                                   max_protein_perc, max_carb_perc, max_fat_perc,
                                   min_protein_perc, min_carb_perc, min_fat_perc)

        res = {
                'last_meal': { 'name': last_meal.food.name  \
                             , 'protein': last_meal.food.protein  \
                             , 'carbs': last_meal.food.carbs  \
                             , 'fat': last_meal.food.fat}  \
               ,'food_sug': list_sugg
               ,'protein_flag': high_protein_flag
               ,'carb_flag': high_carb_flag
               ,'fat_flag': high_fat_flag
            }

        return JsonResponse(res, safe=False)

@csrf_exempt
def auto_complete_function(request):
    qs = Activities.objects.filter(api_description__icontains=request.GET['term'])
    descs = list()
    for desc in qs:
        descs.append(desc.api_description)

    print(descs)
    return JsonResponse(list(descs), safe=False)

@csrf_exempt
def filter_activities(request):
    print(request.GET)
    activity_selected = ActivityCategory.objects.get(id=request.GET['name'])
    qs = Activities.objects.filter(activity_category=activity_selected)

    return JsonResponse(list(qs.values('api_description')), safe=False)

def report(request):
    loggedInUser_food = Profile_food.objects.filter(person=request.user).last()
    context_dict = {}

    week_from_today = date.today() - timedelta(days=7)

    records = Profile_food.objects.filter(date_today__range=[week_from_today, date.today()], person=request.user) \
        .values('calorie_consumed_day', 'protein_consumed_day', 'carbs_consumed_day', 'fats_consumed_day', 'date_today')

    days_list_found = []
    
    records_list = []
    for each_record in records:
        days_list_found.append(each_record['date_today'])
        dict = [
                {'name': 'calories', 'value': each_record['calorie_consumed_day'], 'date': each_record['date_today'].strftime('%Y/%m/%d')},
                {'name': 'protein', 'value': each_record['protein_consumed_day'], 'date': each_record['date_today'].strftime('%Y/%m/%d')},
                {'name': 'carbs', 'value': each_record['carbs_consumed_day'], 'date': each_record['date_today'].strftime('%Y/%m/%d')},
                {'name': 'fat', 'value': each_record['fats_consumed_day'], 'date': each_record['date_today'].strftime('%Y/%m/%d')}
            ]     
        records_list.append(dict)

    sdate = week_from_today  
    edate = date.today()  

    delta = edate - sdate       

    for i in range(delta.days + 1):
        day = sdate + timedelta(days=i)
        day = day.strftime('%Y/%m/%d')
        day_exist = False
        for record in records_list:
            if day == record[0]['date']:
                day_exist = True
  
        if day_exist == False:
            dict = [
                    {'name': 'calories', 'value': 0, 'date': day},
                    {'name': 'protein', 'value': 0, 'date': day},
                    {'name': 'carbs', 'value': 0, 'date': day},
                    {'name': 'fat', 'value': 0, 'date': day}
                ]
            records_list.append(dict)   


    records_json = json.dumps(records_list)
    print(records_list)
    context_dict['records'] = records_json
    return render(request, 'rango/report.html', context=context_dict)

    


