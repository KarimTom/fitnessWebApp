from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rango.models import Food, Profile, PostFood, UserProfile, Category, Video
from rango.forms import ChosenVideoForm, UserForm, UserProfileForm, SelectFoodForm, ProfileForm, CategoryForm, VideoForm
from datetime import date
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

url_food_database = "https://api.edamam.com/api/food-database/v2/parser?app_id=3ac2ff31&app_key=1726dd8e46e8e8027369ba1fc0054a41"
headers = {
    'x-rapidapi-host': "edamam-food-and-grocery-database.p.rapidapi.com",
    'x-rapidapi-key': "591f3078e9mshd96c922a6446c7bp1ff6c3jsn465809415fce"
}

url_nutrition_analysis = "https://api.edamam.com/api/nutrition-data?app_id=c5cfcfef&app_key=9185b3aa75ac918cab425d8adc84e9a9&nutrition-type=logging"
headers = {
    'x-rapidapi-host': "edamam-edamam-nutrition-analysis.p.rapidapi.com",
    'x-rapidapi-key': "591f3078e9mshd96c922a6446c7bp1ff6c3jsn465809415fce"
    }

#querystring = {"ingr": "..", "calories": "100-1000"}


def index(request):
    ##response = requests.request("GET", url_food_database, params=querystring).json()
    # print(len(response['hints']))

    #n = random.sample(range(0,len(response['hints'])-1), 10)
    # print(n)
    # for i in n:
    # print(response['hints'][i])
    # print("\n")
    context_dict = {}
    print(request.user)
    all_videos = Video.objects.all()

    for video in all_videos:
        print(video.title + " , " + str(video.id))
    if request.user.is_authenticated:
        loggedInUser = Profile.objects.filter(person=request.user).last()
        print(loggedInUser)
        calories = loggedInUser.calorie_goal

        if date.today() > loggedInUser.date_today:
            print("Date is different -> Creating new Profile for this date")
            newProfile = Profile.objects.create(
                person=request.user, calorie_goal=calories)
            newProfile.save()

        loggedInUser = Profile.objects.filter(person=request.user).last()
        calories = loggedInUser.calorie_consumed_day
        
        nutrients = Profile.objects.filter(person=request.user) \
            .values('protein_consumed_day', 'carbs_consumed_day', 'fats_consumed_day') \
            .last()

        dict = [{'name': 'protein', 'value': nutrients['protein_consumed_day']},
                {'name': 'carbs', 'value': nutrients['carbs_consumed_day']},
                {'name': 'fats', 'value': nutrients['fats_consumed_day']}]
        nutrients_string = json.dumps(dict)
        print(nutrients_string)
        
        # if calories != 0:
        all_food = PostFood.objects.filter(profile=loggedInUser)
        context_dict['all_food_today'] = all_food
        context_dict['nutrients'] = nutrients_string
        context_dict['calories'] = calories

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
    return redirect(reverse('rango:index'))


def register(request):
    registered = False

    if request.method == 'POST':
        user_form = UserForm(request.POST)
        user_profile_form = UserProfileForm(request.POST)
        profile_form = ProfileForm(request.POST)

        if user_form.is_valid() and user_profile_form.is_valid() and profile_form.is_valid():
            print("Everything is valid -> saving...")
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            userProfile = user_profile_form.save(commit=False)
            userProfile.user = user
            userProfile.save()

            profile = profile_form.save(commit=False)
            profile.person = user
            profile.save()

            registered = True
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
                                                           'registered': registered})


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

    return HttpResponse("Profile page")


def exercises(request):
    context_dict = {}

    category_list = Category.objects.all()
    context_dict['categories'] = category_list

    if request.user.is_authenticated:
        form = VideoForm()

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

        context_dict['videoForm'] = form
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

# check how we are using databases again (we are using filter from now on)


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


def calories(request):
    context_dict = {}
    context_dict['food_suggested'] = None
    context_dict['message'] = None

    form = SelectFoodForm()

    if request.user.is_authenticated:
        loggedInUser = Profile.objects.filter(person=request.user).last()
        print(loggedInUser.calorie_consumed_day)

        calorie_consumed_day = loggedInUser.calorie_consumed_day
        calorie_goal = loggedInUser.calorie_goal

        if calorie_consumed_day/calorie_goal >= 0.5:
            print("Consumed more than half -> time to check the caloric intake and make suggestions...")

            calorie_protein = loggedInUser.protein_consumed_day * 4
            calorie_carbs = loggedInUser.carbs_consumed_day * 4
            calorie_fat = loggedInUser.fats_consumed_day * 9

            print("Protein consumed so far: " + str(calorie_protein))
            print("Carbs consumed so far: " + str(calorie_carbs))
            print("Fat consumed so far: " + str(calorie_fat))

            if calorie_protein/calorie_goal < 0.15:
                print("Little protein... Give suggestions for high protein")
                low_protein_flag = 1
                high_protein_flag = 0
            elif calorie_protein/calorie_goal > 0.25:
                print(
                    "Too much protein... consider food with low protein and high in other sources")
                high_protein_flag = 1
                low_protein_flag = 0
            else:
                print("Good amount of protein so far...")
                low_protein_flag = high_protein_flag = 0

            if calorie_carbs/calorie_goal < 0.5:
                print("Little carbs... Give suggestions for high carbs")
                low_carbs_flag = 1
                high_carbs_flag = 0
            elif calorie_carbs/calorie_goal > 0.65:
                print(
                    "Too much carbs... consider food with low carbs and high in other sources")
                high_carbs_flag = 1
                low_carbs_flag = 0
            else:
                print("Good amount of carbs so far...")
                low_carbs_flag = high_carbs_flag = 0

            if calorie_fat/calorie_goal < 0.5:
                print("Little fat... Give suggestions for high fat")
                low_fat_flag = 1
                high_fat_flag = 0
            elif calorie_fat/calorie_goal > 0.65:
                print(
                    "Too much fat... consider food with low fat and high in other sources")
                high_fat_flag = 1
                low_fat_flag = 0
            else:
                print("Good amount of fat so far...")
                low_fat_flag = high_fat_flag = 0

            # we're weighting food per 100 gram:

            # high carb food is more than 30 (normal is between 15 and 30) (study says 15-30 is high carb food)
            # high fat food is above 17.5 grams
            # high protein food is above 35 (normal is between 20 and 30)

            # low carb food is less than 15
            # low fat food is less than 3g
            # low protein food is less than 15
            if low_protein_flag and low_carbs_flag and low_fat_flag:  # 000
                food_list = []
                context_dict['message'] = "You need to eat more protein, more carbs, and more fat!"
                querystring = {"ingr": "..",
                               "nutrients[CHOCDF]": "15-30",
                               "nutrients[PROCNT]": "25+",
                               "nutrients[FAT]": "17+"}
                response = requests.request(
                    "GET", url_food_database, params=querystring).json()

                n = random.sample(range(0, len(response['hints'])-1), 10)
                print(n)

                for i in n:
                    food = Food.objects.get_or_create(
                        name=response['hints'][i]['food']['label'])[0]
                    food_list.append(food)
                    print(response['hints'][i])
                    print(
                        "Energy: " + str(response['hints'][i]['food']['nutrients']['ENERC_KCAL']))
                    print(
                        "Protein: " + str(response['hints'][i]['food']['nutrients']['PROCNT']))
                    print(
                        "Carbs: " + str(response['hints'][i]['food']['nutrients']['CHOCDF']))
                    print(
                        "Fat: " + str(response['hints'][i]['food']['nutrients']['FAT']))
                    print("\n")

                context_dict['food_suggested'] = food_list
            elif low_protein_flag and low_carbs_flag and high_fat_flag:  # 001
                food_list = []
                context_dict['message'] = "You need to eat more protein, more carbs, with less focus on fat!"
                querystring = {"ingr": "..",
                               "nutrients[CHOCDF]": "15-30",
                               "nutrients[PROCNT]": "35+",
                               "nutrients[FAT]": "3"}
                response = requests.request(
                    "GET", url_food_database, params=querystring).json()

                n = random.sample(range(0, len(response['hints'])-1), 10)
                print(n)

                for i in n:
                    food = Food.objects.get_or_create(
                        name=response['hints'][i]['food']['label'])[0]
                    food_list.append(food)
                    print(response['hints'][i])
                    print(
                        "Energy: " + str(response['hints'][i]['food']['nutrients']['ENERC_KCAL']))
                    print(
                        "Protein: " + str(response['hints'][i]['food']['nutrients']['PROCNT']))
                    print(
                        "Carbs: " + str(response['hints'][i]['food']['nutrients']['CHOCDF']))
                    print(
                        "Fat: " + str(response['hints'][i]['food']['nutrients']['FAT']))
                    print("\n")

                context_dict['food_suggested'] = food_list
            elif low_protein_flag and high_carbs_flag and low_fat_flag:  # 010
                food_list = []
                context_dict['message'] = "You need to eat more protein, more fat, with less focus on carbs!"
                querystring = {"ingr": "..",
                               "nutrients[CHOCDF]": "15",
                               "nutrients[PROCNT]": "35+",
                               "nutrients[FAT]": "17+"}
                response = requests.request(
                    "GET", url_food_database, params=querystring).json()

                n = random.sample(range(0, len(response['hints'])-1), 10)
                print(n)

                for i in n:
                    food = Food.objects.get_or_create(
                        name=response['hints'][i]['food']['label'])[0]
                    food_list.append(food)
                    print(response['hints'][i])
                    print(
                        "Energy: " + str(response['hints'][i]['food']['nutrients']['ENERC_KCAL']))
                    print(
                        "Protein: " + str(response['hints'][i]['food']['nutrients']['PROCNT']))
                    print(
                        "Carbs: " + str(response['hints'][i]['food']['nutrients']['CHOCDF']))
                    print(
                        "Fat: " + str(response['hints'][i]['food']['nutrients']['FAT']))
                    print("\n")

                context_dict['food_suggested'] = food_list
            elif low_protein_flag and high_carbs_flag and high_fat_flag:  # 011
                food_list = []
                context_dict['message'] = "You need to eat more protein, with less focus on carbs, and fat!"
                querystring = {"ingr": "..",
                               "nutrients[CHOCDF]": "15",
                               "nutrients[PROCNT]": "35+",
                               "nutrients[FAT]": "3"}
                response = requests.request(
                    "GET", url_food_database, params=querystring).json()

                n = random.sample(range(0, len(response['hints'])-1), 10)
                print(n)

                for i in n:
                    food = Food.objects.get_or_create(
                        name=response['hints'][i]['food']['label'])[0]
                    food_list.append(food)
                    print(response['hints'][i])
                    print(
                        "Energy: " + str(response['hints'][i['food']]['nutrients']['ENERC_KCAL']))
                    print(
                        "Protein: " + str(response['hints'][i]['food']['nutrients']['PROCNT']))
                    print(
                        "Carbs: " + str(response['hints'][i]['food']['nutrients']['CHOCDF']))
                    print(
                        "Fat: " + str(response['hints'][i]['food']['nutrients']['FAT']))
                    print("\n")

                context_dict['food_suggested'] = food_list
            elif high_protein_flag and low_carbs_flag and low_fat_flag:  # 100
                food_list = []
                context_dict['message'] = "You need to eat more carbs, more fat, with less focus on protein!"
                querystring = {"ingr": "..",
                               "nutrients[CHOCDF]": "15-30",
                               "nutrients[PROCNT]": "15",
                               "nutrients[FAT]": "17+"}
                response = requests.request(
                    "GET", url_food_database, params=querystring).json()

                n = random.sample(range(0, len(response['hints'])-1), 10)
                print(n)

                for i in n:
                    food = Food.objects.get_or_create(
                        name=response['hints'][i]['food']['label'])[0]
                    food_list.append(food)
                    print(response['hints'][i])
                    print(
                        "Energy: " + str(response['hints'][i]['food']['nutrients']['ENERC_KCAL']))
                    print(
                        "Protein: " + str(response['hints'][i]['food']['nutrients']['PROCNT']))
                    print(
                        "Carbs: " + str(response['hints'][i]['food']['nutrients']['CHOCDF']))
                    print(
                        "Fat: " + str(response['hints'][i]['food']['nutrients']['FAT']))
                    print("\n")

                context_dict['food_suggested'] = food_list
            elif high_protein_flag and low_carbs_flag and high_fat_flag:  # 101
                food_list = []
                context_dict['message'] = "You need to eat more carbs, with less focus on protein, and fat!"
                querystring = {"ingr": "..",
                               "nutrients[CHOCDF]": "15-30",
                               "nutrients[PROCNT]": "15",
                               "nutrients[FAT]": "3"}
                response = requests.request(
                    "GET", url_food_database, params=querystring).json()

                n = random.sample(range(0, len(response['hints'])-1), 10)
                print(n)

                for i in n:
                    food = Food.objects.get_or_create(
                        name=response['hints'][i]['food']['label'])[0]
                    food_list.append(food)
                    print(response['hints'][i])
                    print(
                        "Energy: " + str(response['hints'][i]['food']['nutrients']['ENERC_KCAL']))
                    print(
                        "Protein: " + str(response['hints'][i]['food']['nutrients']['PROCNT']))
                    print(
                        "Carbs: " + str(response['hints'][i]['food']['nutrients']['CHOCDF']))
                    print(
                        "Fat: " + str(response['hints'][i]['food']['nutrients']['FAT']))
                    print("\n")

                context_dict['food_suggested'] = food_list
            elif high_protein_flag and high_carbs_flag and low_fat_flag:  # 110
                food_list = []
                context_dict['message'] = "You need to eat more fat, with less focus on protein, and carbs!"
                querystring = {"ingr": "..",
                               "nutrients[CHOCDF]": "15",
                               "nutrients[PROCNT]": "15",
                               "nutrients[FAT]": "17+"}
                response = requests.request(
                    "GET", url_food_database, params=querystring).json()

                n = random.sample(range(0, len(response['hints'])-1), 10)
                print(n)

                for i in n:
                    food = Food.objects.get_or_create(
                        name=response['hints'][i]['food']['label'])[0]
                    food_list.append(food)
                    print(response['hints'][i])
                    print(
                        "Energy: " + str(response['hints'][i]['food']['nutrients']['ENERC_KCAL']))
                    print(
                        "Protein: " + str(response['hints'][i]['food']['nutrients']['PROCNT']))
                    print(
                        "Carbs: " + str(response['hints'][i]['food']['nutrients']['CHOCDF']))
                    print(
                        "Fat: " + str(response['hints'][i]['food']['nutrients']['FAT']))
                    print("\n")

                context_dict['food_suggested'] = food_list
            elif high_protein_flag and high_carbs_flag and high_fat_flag:  # 111
                food_list = []
                context_dict['message'] = "You have eaten good quantity of protein, carbs, and fat... perhaps you could slow down.."
                querystring = {"ingr": "..",
                               "nutrients[CHOCDF]": "15",
                               "nutrients[PROCNT]": "15",
                               "nutrients[FAT]": "3"}
                response = requests.request(
                    "GET", url_food_database, params=querystring).json()

                n = random.sample(range(0, len(response['hints'])-1), 10)
                print(n)

                for i in n:
                    food = Food.objects.get_or_create(
                        name=response['hints'][i]['food']['label'])[0]
                    food_list.append(food)
                    print(response['hints'][i])
                    print(
                        "Energy: " + str(response['hints'][i]['food']['nutrients']['ENERC_KCAL']))
                    print(
                        "Protein: " + str(response['hints'][i]['food']['nutrients']['PROCNT']))
                    print(
                        "Carbs: " + str(response['hints'][i]['food']['nutrients']['CHOCDF']))
                    print(
                        "Fat: " + str(response['hints'][i]['food']['nutrients']['FAT']))
                    print("\n")

                context_dict['food_suggested'] = food_list

        print("Checking if post")
        if request.method == 'POST':
            print("Method is post")
            form = SelectFoodForm(request.POST, instance=loggedInUser)

            if form.is_valid():
                form.save()
        
    

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
                
            label = decode_predictions(predictions, top=10)
            context_dict['predictions'] = label
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

    context_dict['form'] = form
    

    return render(request, 'rango/calories.html', context=context_dict)
