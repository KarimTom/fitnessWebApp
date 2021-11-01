from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rango.models import Food, Profile, PostFood, UserProfile, Category, Video
from rango.forms import ChosenVideoForm, UserForm, UserProfileForm, SelectFoodForm, ProfileForm, CategoryForm, VideoForm
from datetime import date
import datetime
import requests

def index(request):
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
            newProfile = Profile.objects.create(person=request.user)
            newProfile.save()
        
        loggedInUser = Profile.objects.filter(person=request.user).last()
        calories = loggedInUser.calorie_consumed_day

        ##if calories != 0:
        all_food = PostFood.objects.filter(profile=loggedInUser)
        context_dict['all_food_today'] = all_food

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

        if user_form.is_valid() and user_profile_form.is_valid() and profile_form:
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
            print(user_form.errors, profile_form.errors, user_profile_form.errors)
    else:
        user_form = UserForm()
        user_profile_form = UserProfileForm()
        profile_form = ProfileForm()

    return render(request, 'rango/register.html', context={'user_form': user_form, 
                                                           'profile_form': profile_form,
                                                           'user_profile_form' : user_profile_form, 
                                                            'registered': registered})

def weightHeightUpdate(request):
    context_dict = {}
    form = UserProfileForm()

    if request.user.is_authenticated:
        print(request.user)
        loggedInUser = UserProfile.objects.filter(user = request.user).last()
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

## check how we are using databases again (we are using filter from now on)
def workout(request):
    context_dict = {}

    loggedInUser = UserProfile.objects.get_or_create(user=request.user)[0]
    cats = Category.objects.all()

    if request.method == 'POST':
        user_video_add = Video.objects.get_or_create(id=request.POST.get('videoId'))[0]
        print(user_video_add.title)
        print(request.POST.get('videoId'))
        loggedInUser.video.add(user_video_add)

    all_videos = loggedInUser.video.all()
    print(all_videos)

    category_list = []
    for category in cats:
        print("checking category " +category.name)
        category_all_videos = category.videos.all()
        for category_video in category_all_videos:
            for user_video_added in all_videos:
                print(str(category_video.title) + " , " +str(user_video_added.title))
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
    vids_category = category.videos.all()   ##videos of this category

    vids_user = loggedInUser.video.all()    ##videos of the user

    ##logged in user with videos in videos of this category
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

def calories(request):
    context_dict = {}
    ##food_items = Food.objects.all()
    print("View calories")
    form = SelectFoodForm()
    if request.user.is_authenticated:
        loggedInUser = Profile.objects.filter(person=request.user).last()
        print("Checking if post")
        if request.method == 'POST':
            print("Method is post")
            form = SelectFoodForm(request.POST, instance=loggedInUser)
            if form.is_valid():
                form.save()
    
    context_dict['form'] = form
    ##context_dict['food_items'] = food_items
    
    return render(request, 'rango/calories.html', context=context_dict)
