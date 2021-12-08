from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from rango.models import  Food, Profile_food, UserProfile, ActivityCategory, Activities

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'email', 'password',)

class SelectExerciseForm(forms.ModelForm):
    Intensity_estimator = forms.ModelChoiceField(queryset=Activities.objects.all().order_by('api_description'))
    Description = forms.CharField(max_length=256, required=False, label='Describe your activity (optional)')
    Time_in_min = forms.IntegerField(min_value=0)
    class Meta:
        model = Activities
        fields = ('activity_category',)

class SelectExerciseSearchForm(forms.ModelForm):
    Description = forms.CharField(max_length=256, required=False, label='Describe your activity (optional)')
    Time_in_min = forms.IntegerField(min_value=0)
    class Meta:
        model = Activities
        fields = ('api_description', )
    def __init__(self, *args, **kwargs):
        super(SelectExerciseSearchForm, self).__init__(*args, **kwargs)
        self.fields['api_description'].label = 'Search in Database'

class SelectFoodForm(forms.ModelForm):
    class Meta:
        model = Profile_food
        fields = ('meal',)

class AddFoodForm(forms.ModelForm):
    class Meta:
        model = Food
        fields = ('name',)

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile_food
        fields = ('calorie_goal',)
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['calorie_goal'].label = 'Calorie Goal (optional):'

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('gender', 'goal', 'age', 'weight', 'height',)
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['weight'].label = 'weight in kg'
        self.fields['height'].label = 'height in cm'
