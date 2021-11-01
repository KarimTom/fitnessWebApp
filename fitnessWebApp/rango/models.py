from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.db.models.signals import post_save
import requests
from datetime import date
from django.utils import timezone
from django.db.models.fields import NullBooleanField

##url = "https://edamam-edamam-nutrition-analysis.p.rapidapi.com/api/nutrition-data"
url = "https://api.edamam.com/api/nutrition-data?app_id=c5cfcfef&app_key=9185b3aa75ac918cab425d8adc84e9a9&nutrition-type=loggin"
headers = {
    'x-rapidapi-host': "edamam-edamam-nutrition-analysis.p.rapidapi.com",
    'x-rapidapi-key': "591f3078e9mshd96c922a6446c7bp1ff6c3jsn465809415fce"
    }

class Food(models.Model):
    name = models.CharField(max_length=100, null=False)
    ##quantity = models.PositiveIntegerField(null=False, default=0)
    ##calorie = models.FloatField(null=False, default=0)
    person = models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Profile(models.Model):
    person = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE, null=True, blank=True)
    meal = models.CharField(max_length=100, null=True)
    date_today = models.DateField(default=timezone.now)
    calorie_consumed_day = models.FloatField(default=0, null=True)
    calorie_of_meal = models.FloatField(default=0, null=True)
    calorie_goal = models.PositiveIntegerField(default=0)
    all_food_selected_today = models.ManyToManyField(Food,through='PostFood', related_name='inventory')
    
    def save(self, *args, **kwargs):  
        print("Saving Profile")
        ##self.food = Food.objects.get_or_create(name=self.meal, person=self.person)[0]
        if self.meal != None:
            print("Saving Profile")
            ##print(self.food.name)
            if any(char.isdigit() for char in self.meal):
                querystring = {"ingr": self.meal}
            else:
                querystring = {"ingr": str("1 ") + self.meal}
            ##self.calorie_of_meal = (self.food.calorie * self.quantity) / self.food.quantity
            response = requests.request("GET", url, params=querystring).json()
            self.calorie_of_meal = response['calories']
            self.food = Food.objects.get_or_create(name=self.meal, person=self.person)[0]
            print(response)
            print(response['calories'])
            print(response['totalNutrients']['ENERC_KCAL'])
            print(response['totalNutrients']['PROCNT'])
            self.calorie_consumed_day = self.calorie_of_meal + self.calorie_consumed_day
            calories = Profile.objects.filter(person=self.person).last()
            PostFood.objects.create(profile=calories, food=self.food, calorie_amount=self.calorie_of_meal)
            self.food = None
            super(Profile, self).save(*args, **kwargs)
        else:
            super(Profile, self).save(*args,**kwargs)

    def __str__(self):
        return str(self.person.username)

    
    
class PostFood(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    calorie_amount = models.FloatField(default=0, null=True, blank=True)

class Video(models.Model):
    TITLE_MAX_LENGTH = 300
    URL_MAX_LENGTH = 200

    title = models.CharField(max_length=TITLE_MAX_LENGTH, unique=True)
    url = models.URLField()

    def __str__(self):
        return self.title

class UserProfile(models.Model):
    user = models.OneToOneField(User, null=False, on_delete=models.CASCADE)
    weight = models.PositiveIntegerField(null=False, default = 0)
    height = models.PositiveIntegerField(null=False, default = 0)
    BMI = models.DecimalField(null=True, max_digits=5, decimal_places=2)
    video = models.ManyToManyField(Video, default=None, blank=True)

    def save(self, *args, **kwargs):
        print("Saving user profile")
        if self.weight != 0 and self.height != 0:
            self.BMI = (self.weight / self.height) * 100
            super(UserProfile, self).save(*args, **kwargs)
        else:
            super(UserProfile, self).save(*args,**kwargs)

class Category(models.Model):
    NAME_MAX_LENGTH = 128

    name = models.CharField(max_length=NAME_MAX_LENGTH, unique=True)
    slug = models.SlugField(unique=True)
    videos = models.ManyToManyField(Video, default=None, blank=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        self.full_clean()
        super(Category, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

