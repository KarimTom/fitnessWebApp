# from django.contrib.auth.models import User
from django.http.response import JsonResponse
# from django.views import View
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rango.models import Activities, ActivityCategory, Profile_food, Profile_activity, PostFood, UserProfile, PostActivities
from rango.forms import UserForm, UserProfileForm, ProfileForm, SelectExerciseForm, SelectExerciseSearchForm
from rango import api_keys
# from django.utils import timezone
from datetime import date, datetime, timedelta
# from django.db import connections
import json, requests, random
# import tensorflow.compat.v1 as tf
import numpy as np
# from keras import backend as K
from keras.applications import vgg16
from keras.applications.imagenet_utils import decode_predictions
from keras.preprocessing.image import img_to_array, load_img
from tensorflow.python.keras.backend import set_session
from django.views.decorators.csrf import csrf_exempt
from django.utils.datastructures import MultiValueDictKeyError

url_food_database = "https://api.edamam.com/api/food-database/v2/parser"

url_nutrition_analysis = "https://api.edamam.com/api/nutrition-data"

def about(request):
    logout(request)
    return render(request, 'rango/about.html')

## Home page for stating the user's information - daily calories consumed, daily macros consumed
def homePage(request):
    print('Home Page')
    context_dict = {}
    
    ##If user is authenticated - extract all the infos necessary
    if request.user.is_authenticated:
        loggedInUser_food = Profile_food.objects.filter(person=request.user).last()     ##Fetch Database for the food Profile of the user
        calories = loggedInUser_food.calorie_goal       ##extract the calorie goal

        ##Update the Profile on a daily - each day is a new record
        if date.today() != loggedInUser_food.date_today:
            print("Date is different -> Creating new Profile for this date")
            newProfile = Profile_food.objects.create(
                person=request.user, calorie_goal=calories)
            newProfile.save()
            newProfile = Profile_activity.objects.create(
                person=request.user
            )
            newProfile.save()

        ##Fetch the Database for the newest food Profile of the user
        loggedInUser_food = Profile_food.objects.filter(person=request.user).last()

        calories_consumed = loggedInUser_food.calorie_consumed_day
        calorie_goal = loggedInUser_food.calorie_goal
        
        ##extracting macros consumed for the day
        nutrients = Profile_food.objects.filter(person=request.user) \
            .values('protein_consumed_day', 'carbs_consumed_day', 'fats_consumed_day') \
            .last()

        ##JSON for the macros to use them in Javascript
        nutrients_dict = [   
                            {'name': 'protein', 'value': nutrients['protein_consumed_day']},
                            {'name': 'carbs', 'value': nutrients['carbs_consumed_day']},
                            {'name': 'fats', 'value': nutrients['fats_consumed_day']}
                        ]
        nutrients_json = json.dumps(nutrients_dict)
        
        ##JSON for the calories to use them in the Javascript
        calories_dict = [   
                            {'name': 'calorie goal', 'value': calorie_goal, 'filler': 'orange'},
                            {'name': 'calories consumed', 'value': calories_consumed, 'filler': 'green'}
                        ]
        calories_json = json.dumps(calories_dict)

        context_dict['nutrients_info'] = nutrients_json
        context_dict['calories_info'] = calories_json
        
        print('nutrients:') 
        print(nutrients_json)

        print('calories')
        print(calories_json)

    return render(request, 'rango/homePage.html', context=context_dict)


##User Login for authenticating the user
def user_login(request):
    print('login')
    context_dict = {}

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        
        ##if user is authenticated
        if user:
            ##check if the account is active or disabled
            if user.is_active:
                login(request, user)
                print('Welcome!', user)
                return redirect(reverse('rango:homePage'))
            else:
                print('account is disabled')
                return HttpResponse("Your account is disabled.")
        ##invalid login
        else:
            context_dict['error'] = 'Invalid Login!'
            print('Invalid Login')
            
    return render(request, 'rango/login.html', context=context_dict)


##User logging out
def user_logout(request):
    print('Logging out...')
    logout(request)
    return redirect(reverse('rango:about'))


##User register
def register(request):
    print('Register')
    registered = False
    context_dict = {}
    
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        user_profile_form = UserProfileForm(request.POST)
        profile_form = ProfileForm(request.POST)

        ##Check if everything filled is valid
        if user_form.is_valid() and user_profile_form.is_valid() and profile_form.is_valid():
            print("Everything is valid -> saving...")

            ##Calculating BMR
            if request.POST['gender'] == 'male':
                BMR = int(88.362 + 
                         (13.397 * float(request.POST['weight'])) + 
                         (4.799 * float(request.POST['height'])) - 
                         (5.677 * float(request.POST['age']))
                         )
            ##Female
            else:
                BMR = int(447.593 + 
                         (9.247 * float(request.POST['weight'])) + 
                         (3.098 * float(request.POST['height'])) - 
                         (4.330 * float(request.POST['age']))
                         )

            ##Saving profiles - UserProfile, User, Profile_Food, Profile_Activity
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            userProfile = user_profile_form.save(commit=False)
            userProfile.user = user
            userProfile.BMR = BMR
            userProfile.save()

            profile_food = profile_form.save(commit=False)
            profile_food.person = user
            
            Profile_activity.objects.create(person=user)

            ##If user did not choose a custom calorie goal
            if request.POST['calorie_goal'] == '0' or request.POST['calorie_goal'] == '':
                print('User has not chosen a custom calorie goal -> calculating one')
                ##If User has chosen BULK
                if request.POST['goal'] == 'bulk':
                    cal_goal = BMR + (0.15 * BMR)
                ##If User has chosen MAINTENANCE
                elif request.POST['goal'] == 'maintenance':
                    cal_goal = BMR
                ##If User has Chosen FAT LOSS
                else:
                    cal_goal = BMR - 500

                profile_food.calorie_goal = cal_goal

            profile_food.save()

            info_user_profile = UserProfile.objects.get(user=user)
            info_profile_food = Profile_food.objects.get(person=user)

            ##User Successfully registered
            registered = True

            context_dict['BMR'] = BMR
            print('BMR:', BMR)

            context_dict['age'] = info_user_profile.age
            print('age:', info_user_profile.age)

            context_dict['weight'] = info_user_profile.weight
            print('weight:', info_user_profile.weight)

            context_dict['height'] = info_user_profile.height
            print('height:', info_user_profile.height)

            context_dict['BMI'] = info_user_profile.BMI
            print('BMI:', info_user_profile.BMI)

            context_dict['calorie_goal'] = info_profile_food.calorie_goal
            print('calorie goal:', info_profile_food.calorie_goal)

        ##Error in registering - Invalid field somewhere for instance
        else:
            print('Error while registering!')
            print(user_form.errors, profile_form.errors,
                  user_profile_form.errors)
    ##Displaying Forms for Registering
    else:
        print('Displaying Forms')
        user_form = UserForm()
        user_profile_form = UserProfileForm()
        profile_form = ProfileForm()

    return render(request, 'rango/register.html', context={'user_form': user_form,
                                                           'profile_form': profile_form,
                                                           'user_profile_form': user_profile_form,
                                                           'registered': registered,
                                                           'info': context_dict})

##Profile page - Displays the user's information and allow the user to edit their info
def profile(request):
    print('Profile Page')
    context_dict = {}

    user_profile = UserProfile.objects.get(user=request.user) 

    ##Get the latest Food Profile for the user - calorie_goal
    profile_food = Profile_food.objects.filter(person=request.user) \
        .values('calorie_goal') \
        .last()

    context_dict['gender'] = user_profile.gender
    print('gender', user_profile.gender)

    context_dict['BMR'] = user_profile.BMR
    print('BMR:', user_profile.BMR)

    context_dict['BMI'] = user_profile.BMI
    print('BMI:', user_profile.BMI)

    context_dict['age'] = user_profile.age
    print('age:', user_profile.age)

    context_dict['weight'] = user_profile.weight
    print('weight:', user_profile.weight)

    context_dict['height'] = user_profile.height
    print('height:', user_profile.height)

    context_dict['goal'] = user_profile.goal.upper()
    print('goal:', user_profile.goal)
    
    context_dict['calorie_goal'] = profile_food['calorie_goal']
    print('calorie goal:', profile_food['calorie_goal'])

    if request.method == 'POST':
        if request.POST['age']:
            user_profile.age = int(request.POST['age'])
            print('Changed age -> new age: ', user_profile.age)
        if request.POST['weight']:
            user_profile.weight = int(request.POST['weight'])
            print('Changed weight -> new weight: ', user_profile.weight)
        if request.POST['height']:
            user_profile.height = int(request.POST['height'])
            print('Changed height -> new height: ', user_profile.height)
        else:
            user_profile.goal = request.POST['goal']
            print('Changed goal -> new goal: ', user_profile.goal)

        user_profile.save()
        return redirect(reverse('rango:profile'))
        
    return render(request, 'rango/profile.html', context=context_dict)

##bad input flag for Activities page
bad_input_error_exercises = False

##Exercise Page - User logs a form or search through a database, and visualise the activities logged with the estimated calories burned
##                Through a Pie Chart
def activities(request):
    print('In Activities page')
    context_dict = {}

    loggedInUser_activity = Profile_activity.objects.filter(person=request.user).last()
    loggedInUser_food = Profile_food.objects.filter(person=request.user).last()
    loggedInUser_profile = UserProfile.objects.get(user=request.user)
    if request.user.is_authenticated:
        #Displays the two forms - drop down list and searching through a database
        activity_add_form = SelectExerciseForm()
        activity_search_add_form = SelectExerciseSearchForm()

        context_dict['ActivityForm'] = activity_add_form
        context_dict['ActivitySearchForm'] = activity_search_add_form

        #Fetch all the activities performed for today
        li_activities = []
        activities = PostActivities.objects.filter(profile=loggedInUser_activity) \
            .values('description', 'calorie_amount', 'calorie_unit', 'time_min')

        calorie_burned = 0
        for each_activity in activities:
            #Calculating the total calories burned
            calorie_burned = calorie_burned + each_activity['calorie_amount']
            dict = {'name': each_activity['description'], 'calorie_burned': int(each_activity['calorie_amount']),
                    'unit': each_activity['calorie_unit'], 'duration': each_activity['time_min']}
            li_activities.append(dict)
        print('calories burned -> ', calorie_burned)

        #JSON the activities performed for Javascript
        activities_json = json.dumps(li_activities)
        context_dict['activities_info'] = activities_json
        print('activities done: ')
        print(activities_json)

        user_fitness_goal = loggedInUser_profile.goal
        calorie_goal = loggedInUser_food.calorie_goal
        calorie_consumed_day = loggedInUser_food.calorie_consumed_day
        user_weight = loggedInUser_profile.weight
        user_BMR = loggedInUser_profile.BMR

        #Determining the calorie_surplus
        calorie_surplus = 0
        if user_fitness_goal == 'FAT LOSS':

            #If custom calorie_goal > system's calorie_goal
            if calorie_goal > user_BMR - 500:   #user_BMR - 500 is the system's calorie_goal for a user seeking Fat loss
                calorie_surplus = calorie_surplus + ( calorie_goal - (user_BMR - 500) )
            #User ate more than their calorie_goal -> difference is calorie_surplus
            if calorie_goal - calorie_consumed_day < 0:
                calorie_surplus = calorie_surplus + (calorie_consumed_day - calorie_goal)
            
            #If User burned calorie less than the calorie_surplus required to burn -> suggest activities
            if calorie_burned < calorie_surplus:
                calorie_surplus = calorie_surplus - calorie_burned

                print('calories to burn ->', calorie_surplus)
                activity_suggestions = get_activity_suggestions(calorie_surplus, user_weight)
                activity_suggestions_json = json.dumps(activity_suggestions)
                context_dict['suggestions'] = activity_suggestions_json
                print(activity_suggestions_json)
        elif user_fitness_goal == 'MAINTENANCE':  

            #If custom calorie_goal > system's calorie_goal
            if calorie_goal > user_BMR:     #user_BMR is the system's calorie_goal for a user seeking Maintenance
                calorie_surplus = calorie_surplus + ( calorie_goal - user_BMR )
            if calorie_goal - calorie_consumed_day < 0:
                calorie_surplus = calorie_surplus + (calorie_consumed_day - calorie_goal)

            if calorie_burned < calorie_surplus:
                calorie_surplus = calorie_surplus - calorie_burned

                print('calories to burn ->', calorie_surplus)
                activity_suggestions = get_activity_suggestions(calorie_surplus, user_weight)
                activity_suggestions_json = json.dumps(activity_suggestions)
                context_dict['suggestions'] = activity_suggestions_json
                print(activity_suggestions_json)
        else:

            #If custom calorie_goal > system's calorie_goal
            if calorie_goal > user_BMR + (0.15 * user_BMR): #user_BMR + user_BMR * 0.15 is the system's calorie_goal for a user seeking Bulk
                calorie_surplus = calorie_goal - (user_BMR + 500)
            if calorie_goal - calorie_consumed_day < 0:
                calorie_surplus = calorie_surplus + (calorie_consumed_day - calorie_goal)

            if calorie_burned < calorie_surplus:
                calorie_surplus = calorie_surplus - calorie_burned

                print('calories to burn ->', calorie_surplus)
                activity_suggestions = get_activity_suggestions(calorie_surplus, user_weight)
                activity_suggestions_json = json.dumps(activity_suggestions)
                context_dict['suggestions'] = activity_suggestions
                print(activity_suggestions_json)
            
        #Check for Error when user logging the activity
        global bad_input_error_exercises
        if bad_input_error_exercises == True:
            print('Bad input!!!')
            context_dict['error'] = 'That doesn''t seem right! Try filling out the form on the left'
            bad_input_error_exercises = False
            
    return render(request, 'rango/activities.html', context=context_dict)

##bad input flag for photo recognition
bad_input_photo_recognition = False

##Nutrition Page - User logs their meal either by typing or using meal photo recognition
def nutrition(request):
    context_dict = {}
    context_dict['last_meal'] = None
    context_dict['food_sug'] = None
    context_dict['meals'] = None
    context_dict['predictions'] = None

    context_dict['high_protein_flag'] = context_dict['high_carb_flag'] = context_dict['high_fat_flag'] = None

    if request.user.is_authenticated:
        global bad_input_photo_recognition
        if bad_input_photo_recognition == True:
            print('Photo was not recognised as a meal!!!')
            context_dict['error'] = 'That doesn''t seem to be a meal! Try again'
            bad_input_photo_recognition = False

        loggedInUser_food = Profile_food.objects.filter(person=request.user).last()
        print(loggedInUser_food.calorie_consumed_day)

        user_profile = UserProfile.objects.get(user=request.user)
        goal = user_profile.goal

        #Fetches all the meals taken in this day
        meals_taken = PostFood.objects.filter(profile=loggedInUser_food)
        #Fetches last meal
        last_meal = PostFood.objects.filter(profile=loggedInUser_food).last()
        
        file = None

        #User uploaded a photo for meal photo recognition
        if request.method == "POST":  
            try:
                request.FILES["imageFile"]
                file = request.FILES["imageFile"]
                print(file.name)
                file_name = default_storage.save(file.name, file)
                file_url = default_storage.path(file_name)
                
                #load the photo uploaded
                image = load_img(file_url, target_size=(224, 224))
                #digitising the image
                numpy_array = img_to_array(image)
                image_batch = np.expand_dims(numpy_array, axis=0)
                processed_image = vgg16.preprocess_input(image_batch.copy())

                
                set_session(settings.SESS)
                
                #predict the category of the photo (e.g., what meal it is - pizza, donut, etc..)
                predictions = settings.IMAGE_MODEL.predict(processed_image)
                    
                labels = decode_predictions(predictions, top=5)

                #filter the label to pass it to the API of Nutrition Analysis
                for each_label in labels:
                    for prediction in each_label:
                        type_predicted = prediction[1]
                        if '_' in type_predicted:
                            filter_string = str.split(type_predicted, '_')
                            print(filter_string)
                            type_predicted = ''
                            for strings in filter_string:
                                type_predicted += strings + ' '
                                print('photo predicted: ', type_predicted)
                        #Call API Nutrition Analysis with parameters
                        querystring = {"app_id": api_keys.headers_nutrition_analysis['app_id'],
                                    "app_key": api_keys.headers_nutrition_analysis['app_key'],
                                    "ingr": "100 gr " +type_predicted
                                    }
                        response = requests.request("GET", url_nutrition_analysis, params=querystring).json()

                        #If picture is a food -> save
                        if response['calories'] != 0:
                            print("meal predicted: " ,type_predicted)

                            print("Energy: " +str(response['totalNutrients']['ENERC_KCAL']['quantity']))
                            print("Protein: " +str(response['totalNutrients']['PROCNT']['quantity']))
                            print("Carbs: " +str(response['totalNutrients']['CHOCDF']['quantity']))
                            print("Fat: " +str(response['totalNutrients']['FAT']['quantity']))

                            loggedInUser_food.meal = type_predicted
                            loggedInUser_food.save()
                            return redirect(reverse('rango:nutrition'))
                        else:
                            context_dict['predictions'] = type_predicted

                bad_input_photo_recognition = True
                return redirect(reverse('rango:calories'))
            #If nothing was uploaded
            except KeyError:
                print("Nothing was uploaded")

        else:
            if last_meal:  
                dict = {'name': last_meal.food.name,
                        'protein': last_meal.food.protein,
                        'carbs': last_meal.food.carbs,
                        'fat': last_meal.food.fat
                        }
                last_meal_json = json.dumps(dict)
                context_dict['last_meal'] = last_meal_json
                
                print('last meal: ')
                print(last_meal_json)

                calories = last_meal.food.calorie

                #Assign range of percentages of macros for user on each fitness goal
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

                #Check if last meal had an excess of certain macro depending on each user's fitness goal
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

                #Get food suggestions
                list_sugg = get_food_suggestions(calories, 
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
            
            print('meals taken: ')
            print(meals)
            context_dict['meals'] = meals                    

    return render(request, 'rango/nutrition.html', context=context_dict)

##Processing the activity logged by the User
def activity_process(request):
    print('processing activity')
    loggedInUser_activity = Profile_activity.objects.filter(person=request.user).last()
    #Assuming the user logged their activity through filling the form
    try:
        activity_selected = ActivityCategory.objects.get(id=request.POST['activity_category'])
        activity_overall= Activities.objects.get(activity_category=activity_selected, api_description=request.POST['Intensity_estimator'])
    #Exception if user filled by the search method
    except MultiValueDictKeyError:
        #Processing the acitivity logged by the User
        try:
            activity_overall = Activities.objects.get(api_description=request.POST['api_description'])
        #Can't find the MET values and intensity estimating -> bad input error
        except Activities.DoesNotExist:
            global bad_input_error_exercises
            bad_input_error_exercises = True
            return redirect(reverse('rango:activities'))

    #input was correct -> further processing
    time_in_min = request.POST['Time_in_min']
    description = request.POST['Description']

    loggedInUser_activity.activity = activity_overall
    loggedInUser_activity.time_min = int(float(time_in_min))
    if description != '':
        loggedInUser_activity.description = description
    else:
        loggedInUser_activity.description = 'No description provided'

    #Saving the activity logged by the user
    loggedInUser_activity.save()
    return redirect(reverse('rango:activities'))

##Processing the meal logged by the user - done through an ajax request 
@csrf_exempt
def meal_process(request):

    if request.is_ajax() and request.user.is_authenticated and request.method == 'POST':
        loggedInUser = Profile_food.objects.filter(person=request.user).last()

        user_profile = UserProfile.objects.get(user=request.user)
        goal = user_profile.goal

        meal = request.POST['name']

        profile = Profile_food.objects.filter(person=request.user).last()
        profile.meal = meal
        #Saving meal with the help of Edamam API
        try:
            profile.save()
        #Bad input error
        except KeyError:
            dict = {'error': 'That doesn''t seem right! Please check the meal again'}
            return JsonResponse(dict, safe=False)
        
        last_meal = PostFood.objects.filter(profile=loggedInUser).last()
        calories = last_meal.food.calorie

        #Distributing the correct percentages of each macro for meal analysing and food suggesting
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
        
        #Checking if the meal has an excess of certain macro
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

        list_sugg = get_food_suggestions(calories, 
                                         high_protein_flag, high_carb_flag, high_fat_flag,
                                         max_protein_perc, max_carb_perc, max_fat_perc,
                                         min_protein_perc, min_carb_perc, min_fat_perc)

        #JSON of the variables to return - last meal is the last meal the user had
        #                                - food sug is the suggested food for the user based on the last meal
        #                                - protein/carb/fat flag are the flags which help the system in know which macro was an excess in the meal
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

##Auto complete to help the user in searching the activity database easily
@csrf_exempt
def auto_complete_function(request):
    qs = Activities.objects.filter(api_description__startswith=request.GET['term'])
    descs = list()
    for desc in qs:
        descs.append(desc.api_description)

    print(descs)
    return JsonResponse(list(descs), safe=False)

##Filtering activities depending on what the user has chosen from the drop down category list to make it easier for the user to log their activities
@csrf_exempt
def filter_activities(request):
    print(request.GET)
    activity_selected = ActivityCategory.objects.get(id=request.GET['name'])
    qs = Activities.objects.filter(activity_category=activity_selected)

    return JsonResponse(list(qs.values('api_description')), safe=False)

##Weekly calories/macros report
def report(request):
    loggedInUser_food = Profile_food.objects.filter(person=request.user).last()
    context_dict = {}

    #Get the week from today date
    week_from_today = date.today() - timedelta(days=7)

    #Get the records within a week
    records = Profile_food.objects.filter(date_today__range=[week_from_today, date.today()], person=request.user) \
        .values('calorie_consumed_day', 'protein_consumed_day', 'carbs_consumed_day', 'fats_consumed_day', 'date_today')

    #Save the days found in the system (Days found are the days where the user logged in to the system)
    days_list_found = []
    
    #Save the records found
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

    #Start date is week from today - End date is today
    #Check all the date of found records and add the dates missing with 0 macros and 0 calories because User did not log in
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


##Food suggestions based on user's last meal logged
##Algorithm suggested: If meal is high in certain macro (i.e., fat, carb, protein)
##                          Calculate the new percentage of the macro
##                          Example: max percentage of protein in a meal is 35% - the last meal had 45% protein
##                                   new percentage is 35% - (45% - 35%) = 25%
##                                   If the Excess was higher than the original percentage (e.g., 85% protein)
##                                   new percentage is 35% - (85% - 35%) = -5% - assign the next meal to have 3g of protein (3g represents a negligible amount of protein)
##                                   Meal will be rich in other macros therefore
##                     else 
##                          Leave the percentage as its default
##                     Check for meals having the calculated percentages of the macros

##high_protein_flag, high_carb_flag, high_fat_flag are the excess percentage of the macros (0 if within normal range)
##max_protein_perc, max_carb_perc, max_fat_perc are the max percentage allowed for a macro inside a meal
##min_protein_perc, min_carb_perc, min_fat_perc are the min percentage allowed for a macro inside a meal
##calories is the calories of the last meal
def get_food_suggestions(calories, 
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

    print("Max Protein Percentage: Max Carbs Percentage: Max Fat Percentage:")
    print(max_protein_percentage,max_carb_percentage,max_fat_percentage)

    print("New Protein Max percentage: New Carbs Max Percentage: New fat Max Percentage:")
    print(max_protein_percentage - high_protein_flag,max_carb_percentage - high_carb_flag,max_fat_percentage - high_fat_flag)

    if high_protein_flag != 0:

        #Excess in protein and new percentage is still too much - assign a negligible amount of protein
        if max_protein_percentage - high_protein_flag < 0:
            min_protein_gr = 3
            max_protein_gr = int(0.15 * calories / 4)
            min_protein_gr = min(min_protein_gr, max_protein_gr)
            max_protein_gr = max(min_protein_gr, max_protein_gr)
            protein_qtity = str(min_protein_gr) + "-" + str(max_protein_gr)
        #Excess in protein and new percentage is less than the minimum protein percentage - assign the new percentage to be minimum and the minimum to be maximum
        elif max_protein_percentage - high_protein_flag < min_protein_percentage:
            min_protein_gr = 3
            protein_cal = (max_protein_percentage - high_protein_flag) * calories
            max_protein_gr = int(protein_cal / 4)
            min_protein_gr = min(min_protein_gr, max_protein_gr)
            max_protein_gr = max(min_protein_gr, max_protein_gr)
            protein_qtity = str(min_protein_gr) + "-" + str(max_protein_gr)
        #Excess in protein and new percentage is bigger than minimum protein percentage
        else:
            protein_cal = (max_protein_percentage - high_protein_flag) * calories
            max_protein_gr = int(protein_cal / 4)
            protein_qtity = str(min_protein_gr) + "-" + str(max_protein_gr)
    
    #No Excess
    else:
        protein_qtity = str(min_protein_gr) + "-" +str(max_protein_gr)

    if high_carb_flag != 0:

        #Excess in carbs and new percentage is still too much - assign a negligible amount of carbs
        if max_carb_percentage - high_carb_flag < 0:
            min_carb_gr = 3
            max_carb_gr = int(0.15 * calories / 4)
            min_carb_gr = min(min_carb_gr, max_carb_gr)
            max_carb_gr = max(min_carb_gr, max_carb_gr)
            carb_qtity = str(min_carb_gr) + "-" + str(max_carb_gr)
        #Excess in carbs and new percentage is less than the minimum carbs percentage - assign the new percentage to be minimum and the minimum to be maximum
        elif max_carb_percentage - high_carb_flag < min_carb_percentage:
            min_carb_gr = 3
            carb_cal = (max_carb_percentage - high_carb_flag) * calories
            max_carb_gr = int(carb_cal / 4)
            min_carb_gr = min(min_carb_gr, max_carb_gr)
            max_carb_gr = max(min_carb_gr, max_carb_gr)
            carb_qtity = str(min_carb_gr) + "-" + str(max_carb_gr)
        #Excess in carbs and new percentage is bigger than minimum carbs percentage
        else:
            carb_cal = (max_carb_percentage - high_carb_flag) * calories
            max_carb_gr = int(carb_cal / 4)
            carb_qtity = str(min_carb_gr) + "-" + str(max_carb_gr)

    #No Excess
    else:
        carb_qtity = str(min_carb_gr) + "-" +str(max_carb_gr)
    
    if high_fat_flag != 0: 

        #Excess in fat and new percentage is still too much - assign a negligible amount of fat
        if max_fat_percentage - high_fat_flag < 0:
            min_fat_gr = 3
            max_fat_gr = int(0.15 * calories / 9)
            min_fat_gr = min(min_fat_gr, max_fat_gr)
            max_fat_gr = max(min_fat_gr, max_fat_gr)
            fat_qtity = str(min_fat_gr) + "-" + str(max_fat_gr)
        #Excess in fat and new percentage is less than the minimum fat percentage - assign the new percentage to be minimum and the minimum to be maximum
        elif max_fat_percentage - high_fat_flag < min_fat_percentage:
            min_fat_gr = 3
            fat_cal = (max_fat_percentage - high_fat_flag) * calories
            max_fat_gr = int(fat_cal / 9)
            min_fat_gr = min(min_fat_gr, max_fat_gr)
            max_fat_gr = max(min_fat_gr, max_fat_gr)
            fat_qtity = str(min_fat_gr) + "-" + str(max_fat_gr)
        #Excess in fat and new percentage is bigger than minimum fat percentage
        else:
            fat_cal = (max_fat_percentage - high_fat_flag) * calories
            max_fat_gr = int(fat_cal / 9)
            fat_qtity = str(min_fat_gr) + "-" + str(max_fat_gr)
    #No Excess
    else:
        fat_qtity = str(min_fat_gr) + "-" +str(max_fat_gr)

    #Print the calculated maco grams
    print('protein:' +protein_qtity)
    print('carbs:' +carb_qtity)
    print('fat:' +fat_qtity)

    #API for Food Database Call with generic meals as the category for food searched
    #generic meals is the best category to search for good quality food according to Food Database API
    try:
        querystring = {
                    "app_id": api_keys.headers_food_database['app_id'],
                    "app_key": api_keys.headers_food_database['app_key'],
                    "ingr": "..",
                    "category": ["generic-meals"],
                    "nutrients[CHOCDF]": carb_qtity,
                    "nutrients[PROCNT]": protein_qtity,
                    "nutrients[FAT]": fat_qtity
                    }
        
        
        response = requests.request(
                        "GET", url_food_database, params=querystring).json()


        n = random.sample(range(0, len(response['hints'])-1), 5)
    #No Food found for this category - Try with all categories to expand the search (generic food, generic meals, fast food, etc..)
    except ValueError:
        print('no food with category -generic meals- found -> expanding search...')
        try:
            querystring = {
                        "app_id": api_keys.headers_food_database['app_id'],
                        "app_key": api_keys.headers_food_database['app_key'],
                        "ingr": "..",
                        "nutrients[CHOCDF]": carb_qtity,
                        "nutrients[PROCNT]": protein_qtity,
                        "nutrients[FAT]": fat_qtity
                        }
            
            
            response = requests.request(
                            "GET", url_food_database, params=querystring).json()


            n = random.sample(range(0, len(response['hints'])-1), 5)
        #No Food found - Try to expand the search by extending the range of all macros.
        except ValueError:
            print('no food with specific macros found -> expanding search...')
            querystring = {
                        "app_id": api_keys.headers_food_database['app_id'],
                        "app_key": api_keys.headers_food_database['app_key'],
                        "ingr": "..",
                        "nutrients[CHOCDF]": str(0) + "-" + str(max_carb_gr),
                        "nutrients[PROCNT]": str(0) + "-" + str(max_protein_gr),
                        "nutrients[FAT]": str(0) + "-" + str(max_fat_gr)
                        }
            
            
            response = requests.request(
                            "GET", url_food_database, params=querystring).json()


            #Shuffling through the list of food fetched - distinct shuffle
            n = random.sample(range(0, len(response['hints'])-1), 5)

    food_list = []
    print('food suggested...')
    #printing each food selected with the shuffle
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

##Suggesting Activities for the user - based on their information and their progress throughout the day
##Any caloric surplus must be burned - This is determined based on their calorie_goal against the system's suggestion calorie_goal
##                                     calories_consumed against calorie_goal, and user fitness target e.g., bulk, fat loss, etc..
def get_activity_suggestions(calorie_surplus, weight):
    #for fat loss -> get the met value of activities that burns (500 - calorie_goal - calorie_consumed_day) in an interval of 30 to 50 mins
    #                500 - (calorie_goal + calorie_consumed_day) because research suggest that 500 deficit a week help the client to loose
    #                1 pound of fat a week
    #for maintenance -> get the met value of activities that burns calories surplus in an interval of 30 to 50 mins
    #for bulk -> only get the met value of activities that burns calorie surplus in an interval of 30 to 50 mins

    #Research suggest that a 30 to 50 min workout a day is good for health - Interval chosen is from 30 to 50 mins
    time_min = [30, 40, 50]

    #Algorithm suggested - calculate a MET value, fetch the database for activities with the MET calculated
    #                      if Found, exit the loop because activities are found
    #                      else, activities are not found for a specific MET - divide calorie_surplus by 2 and repeat until activities are found
    #                      Sometimes, Activities cannot be found for a specific MET Value, thus change the calorie_surplus
    #                      and Repeat until found.
    while True:
        met_value = []
        met_time = {}

        ##Get activities related to sports
        activities = ['running', 'bicycling', 'sports']
        activities_models = ActivityCategory.objects.filter(name__in =activities) \
                                .values('id', 'name')
        ##Get the ID of the activity_categories
        id_activities_models = []
        for activity_model in activities_models:
            id_activities_models.append(activity_model['id'])

        #Calculate a MET Value having a specific time and weight and calories to burn
        #Formula for calculating calories_burned from an activity = ( MET * 3.5 * weight * time[in min] / 200 )
        #Reversing Formula -> MET = calories_burned * 200 / (weight * 3.5 * time[in min])
        for time in time_min:
            met_calculated = int( (calorie_surplus * 200) / (weight * 3.5 * time) )
            met_value.append(met_calculated)
            met_time[met_calculated] = time
        
        print('met calculated for each time:')
        print(met_time)

        activities_fetched = Activities.objects.filter(activity_category__in=id_activities_models, met_value__in=met_value) \
                                .values('api_description', 'activity_category', 'met_value')
        suggestions = []

        #Activities fetched - Save the info necessary
        for activity in activities_fetched:
            dict = {'activity': activity['api_description'],
                    'category': activity['activity_category'],
                    'MET': activity['met_value'],
                    'Time': met_time[activity['met_value']],
                    'Calories_burned': calorie_surplus
                }
            print('Activity:')
            print(dict)
            if len(suggestions) < 5:
                suggestions.append(dict)
            else:
                break

        if len(suggestions) != 0:
            break
        else:
            calorie_surplus = int(calorie_surplus/2)
            
    #go to databse -> fetch activities with selected met values randomly and display them (5 activities suggestion distributed over interval)
    return suggestions

    


