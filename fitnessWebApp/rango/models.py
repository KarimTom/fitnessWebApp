from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.db.models.signals import post_save
import requests
from datetime import date
from django.utils import timezone
from django.db.models.fields import NullBooleanField

url_nutrition_analysis = "https://api.edamam.com/api/nutrition-data"
headers_nutrition_analysis = {
    'app_id': "c5cfcfef",
    'app_key': "9185b3aa75ac918cab425d8adc84e9a9"
}

url_calorie_track = "https://fitness-calculator.p.rapidapi.com/burnedcalorie"
headers = {
    'x-rapidapi-host': "fitness-calculator.p.rapidapi.com",
    'x-rapidapi-key': "591f3078e9mshd96c922a6446c7bp1ff6c3jsn465809415fce"
    }


class Food(models.Model):
    name = models.CharField(max_length=100, null=False)
    calorie = models.FloatField(null=True, default=0)
    protein = models.PositiveIntegerField(null=False, default=0)
    carbs = models.PositiveIntegerField(null=False, default=0)
    fat = models.PositiveIntegerField(null=False, default=0)
    person = models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class ActivityCategory(models.Model):
    NAME_MAX_LENGTH = 128

    name = models.CharField(max_length=NAME_MAX_LENGTH)

    class Meta:
        verbose_name_plural = 'Activity_Categories'

    def __str__(self):
        return self.name

class Activities(models.Model):
    API_DESCRIPTION_MAX_LENGTH = 256
    QUERY_MAX_LENGTH = 32

    api_description = models.CharField(max_length=API_DESCRIPTION_MAX_LENGTH)
    intensity_level = models.PositiveIntegerField(null=False, default = 0)
    met_value = models.FloatField(null=False, default= 1)
    query_id = models.CharField(max_length=QUERY_MAX_LENGTH)
    activity_category = models.ForeignKey(ActivityCategory, on_delete=models.CASCADE)

    class Meta:
         verbose_name_plural = 'Activities'

    def __str__(self):
        return self.api_description


class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('male','MALE'),
        ('female', 'FEMALE'),
    )

    GOAL_CHOICES = (
        ('bulk', 'BULK'),
        ('maintenance', 'MAINTENANCE'),
        ('fat loss', 'FAT LOSS')
    )

    user = models.OneToOneField(User, null=False, on_delete=models.CASCADE)
    age = models.PositiveIntegerField(null=False, blank=False, default=0)
    gender = models.CharField(max_length=32, choices=GENDER_CHOICES, default='not specified')
    goal = models.CharField(max_length=32, choices=GOAL_CHOICES, default= 'not specified') 
    BMR = models.PositiveIntegerField(null=False, blank=False, default=0)
    weight = models.PositiveIntegerField(null=False, default = 0)
    height = models.PositiveIntegerField(null=False, default = 0)
    BMI = models.DecimalField(null=True, max_digits=5, decimal_places=2)

    def save(self, *args, **kwargs):
        print("Saving user profile")
        
        #BMI = Weight / Height * Height * 10000 -> estimating fat percentage of the user
        if self.weight != 0 and self.height != 0:
            self.BMI = (self.weight / (self.height * self.height) ) * 10000
            super(UserProfile, self).save(*args, **kwargs)
        else:
            super(UserProfile, self).save(*args,**kwargs)


class Profile_activity(models.Model):
    person = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    date_today = models.DateField(default=timezone.now)
    calorie_burned = models.PositiveIntegerField(default=0, null=True)
    activity = models.ForeignKey(Activities, on_delete=models.CASCADE, null=True, blank=True)
    time_min = models.PositiveIntegerField(default=0, null=True, blank=True)
    cal_unit = models.CharField(max_length=32, default = 'cal', null=True, blank=True)
    description = models.CharField(max_length=256, null=False, blank=False, default='No description provided')
    all_activities = models.ManyToManyField(Activities, through='PostActivities', related_name='activities_inventory')

    def save(self, *args, **kwargs):
        if self.activity != None:
            #Estimate the calories burned -> Activity's MET * weight * 3.5 / 200 * Time in min
            loggedInUser = UserProfile.objects.get(user=self.person)
            weight = loggedInUser.weight
            met_value = self.activity.met_value

            cal_burned = (met_value*weight*3.5/200)*self.time_min

            self.calorie_burned += self.calorie_burned + int(cal_burned)
            self.cal_unit = 'calorie'

            calories = Profile_activity.objects.filter(person=self.person).last()
            
            #Keep track of the activity by saving it in the Database for this user
            PostActivities.objects.create(profile=calories, activities=self.activity \
                                         ,calorie_amount=cal_burned, description=self.description \
                                         ,calorie_unit=self.cal_unit, time_min=self.time_min)
                
            self.activity = None
            self.time_min = None

            super(Profile_activity, self).save(*args,**kwargs)
        else:
            super(Profile_activity, self).save(*args,**kwargs)

    def __str__(self):
        return str(self.person.username)

class Profile_food(models.Model):
    person = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    date_today = models.DateField(default=timezone.now)
    carbs_consumed_day = models.PositiveIntegerField(default=0, null=True)  
    fats_consumed_day = models.PositiveIntegerField(default=0, null=True)    
    protein_consumed_day = models.PositiveIntegerField(default=0, null=True) 
    calorie_consumed_day = models.FloatField(default=0, null=True) 
    calorie_goal = models.PositiveIntegerField(default=0, blank=True, null=True)
    food = models.ForeignKey(Food, on_delete=models.CASCADE, null=True, blank=True)
    meal = models.CharField(max_length=100, null=True)
    all_food_selected_today = models.ManyToManyField(Food,through='PostFood', related_name='inventory')

    def save(self, *args, **kwargs):  
        print("Saving Profile")

        if self.meal != None:
            print("Saving Profile")
            
            #Check if the meal logged in has a weight (i.e., 100 gr, 200 gr, etc..)
            if any(char.isdigit() for char in self.meal):
                
                #Nutrtion Analysis API with the following parameters
                querystring = {"app_id": headers_nutrition_analysis['app_id'],
                               "app_key": headers_nutrition_analysis['app_key'],
                               "ingr": self.meal
                               }
            else:
                #Nutrition Analysis API with default size of 100 gr
                querystring = {"app_id": headers_nutrition_analysis['app_id'],
                               "app_key": headers_nutrition_analysis['app_key'],
                               "ingr": '100 gr ' + str(self.meal)
                               }

            response = requests.request("GET", url_nutrition_analysis, params=querystring).json()
            
            self.food = Food.objects.create(name=self.meal, person=self.person \
                                                   , protein=int(response['totalNutrients']['PROCNT']['quantity']) \
                                                   , carbs =int(response['totalNutrients']['CHOCDF']['quantity']) \
                                                   , fat = int(response['totalNutrients']['FAT']['quantity'])
                                                   , calorie = int(response['calories']))

            print(response['calories'])
            print("Energy: " +str(response['totalNutrients']['ENERC_KCAL']['quantity']))
            print("Protein: " +str(response['totalNutrients']['PROCNT']['quantity']))
            print("Carbs: " +str(response['totalNutrients']['CHOCDF']['quantity']))
            print("Fat: " +str(response['totalNutrients']['FAT']['quantity']))

            self.carbs_consumed_day = self.carbs_consumed_day + response['totalNutrients']['CHOCDF']['quantity']
            self.fats_consumed_day = self.fats_consumed_day + response['totalNutrients']['FAT']['quantity']
            self.protein_consumed_day = self.protein_consumed_day + response['totalNutrients']['PROCNT']['quantity']
            self.calorie_consumed_day = response['calories'] + self.calorie_consumed_day
            
            calories = Profile_food.objects.filter(person=self.person).last()

            #Save the meal logged for this user
            PostFood.objects.create(profile=calories, food=self.food \
                                   ,calorie_amount=response['calories'])
            self.food = None
            self.meal = None

            super(Profile_food, self).save(*args, **kwargs)

        else:
            super(Profile_food, self).save(*args,**kwargs)

    def __str__(self):
        return str(self.person.username)

class PostFood(models.Model):
    profile = models.ForeignKey(Profile_food, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    calorie_amount = models.FloatField(default=0, null=True, blank=True)

class PostActivities(models.Model):
    UNIT_MAX_LENGTH = 32
    DESCRIPTION_MAX_LENGTH = 256

    profile = models.ForeignKey(Profile_activity, on_delete=models.CASCADE)
    activities = models.ForeignKey(Activities, on_delete=models.CASCADE)
    calorie_amount = models.FloatField(default=0, null=True, blank=True)
    time_min = models.PositiveIntegerField(default=0, null=False, blank=False)
    calorie_unit = models.CharField(max_length=UNIT_MAX_LENGTH, null=False, blank=False)
    description = models.CharField(max_length=DESCRIPTION_MAX_LENGTH, default='no description', null=False, blank=False)

    class Meta:
        verbose_name_plural = 'PostActivities'

