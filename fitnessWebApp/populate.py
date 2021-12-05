import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'fitnessWebApp.settings')
import requests
import django
django.setup()
from rango.models import ActivityCategory, Activities

def populate():
    url = "https://fitness-calculator.p.rapidapi.com/activities"

    headers = {
        'x-rapidapi-host': "fitness-calculator.p.rapidapi.com",
        'x-rapidapi-key': "591f3078e9mshd96c922a6446c7bp1ff6c3jsn465809415fce"
    }

    for i in range(1, 10):
        querystring = {"intensitylevel":str(i)}

        response = requests.request("GET", url, headers=headers, params=querystring).json()
        data = response['data']
        for each_activity in data:
            add_activity(each_activity['activity'], each_activity['description'], 
                         each_activity['intensityLevel'], each_activity['id'],
                         each_activity['metValue'] )
            print("Success")


def add_activity(activity_name, activity_api_description, activity_intensity_level, activity_query_id, activity_met_value):
    activity_category_object = ActivityCategory.objects.get_or_create(name=activity_name)[0]
    activity_category_object.save()

    activity = Activities.objects.get_or_create(api_description=activity_api_description, intensity_level=activity_intensity_level,  
                                                query_id=activity_query_id, activity_category=activity_category_object, 
                                                met_value=activity_met_value)[0]
    activity.save()
    
    return activity

if __name__ == '__main__':
    print('Starting Rango population script...')
    populate()
