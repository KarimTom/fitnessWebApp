from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from rango.models import  Food, Profile_food, UserProfile, Category, Video, ActivityCategory, Activities

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

class CategoryForm(forms.ModelForm):
    name = forms.CharField(max_length=Category.NAME_MAX_LENGTH, help_text="Please enter the category name.")
    slug = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Category
        fields = ('name',)

class ChosenVideoForm(forms.ModelForm):
    class meta:
        model = Video
        exclude = ('category',)

class VideoForm(forms.ModelForm):
    title = forms.CharField(max_length=Video.TITLE_MAX_LENGTH)
    url = forms.URLField(max_length=300)
    
    class Meta:
        model = Video
        exclude = ('category',)

    def clean(self):
        cleaned_data = self.cleaned_data
        url = cleaned_data.get('url')

        string = str(url)
        stringList = string.split('.com/')

        string2 = stringList[0] + ".com/embed/" + stringList[1]
        string2 = string2.replace("watch?v=","")
        url = string2
        print(url)
        cleaned_data['url'] = url

        if url and not url.startswith(('http://') or ('https://')):
            url = f'http://{url}'
            cleaned_data['url'] = url 

        return cleaned_data