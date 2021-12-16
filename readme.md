# MyFitDiary: A Fitness Application People Who Care About their Health

This Project aims for **tracking: calories, macros, and activities.**.
This project uses **d3.js** for data visualisation. It presents: **pie charts, bars, and a user-interactive graph**.

## Requirements:

To launch this project, you will need to have the following mentioned libraries:
- Django **3.2.10** (e.g., pip install Django==3.2.10)
- Django_extensions **3.1.5** (e.g., pip install Django_extensions==3.1.5)
- Tensorflow **2.7.0** (e.g., pip install Tensorflow==2.7.0)
- Pillow **8.4.0** (e.g., pip install Pillow==8.4.0)
  
# Running the application:

To run the project on the device, execute the following commands:
- python manage.py makemigration
- python manage.py migrate --run-syncdb
- python save_activities_db.py (**connect to fitnescalculator API and save all the activities in the database**)
- python manage.py runserver (**VGG16 will be downloaded if this device is running this project for the first time, then it will run**)

## Demo:

This video presents a demo of the following developed product:
[MyFitDiary demo] (https://www.youtube.com/watch?v=NN6yH8ndUOM&ab_channel=KarimTom)


# Note:

### API Keys were hidden for security reasons. if you would like to use Edamam API - Head over to https://www.edamam.com/ and follow their instructions for claiming keys. Afterwards, replace in the code everything that starts with **api_keys.headers_nutrition_analysis['app_key'] and headers_nutrition_analysis['app_id']** with the keys.
