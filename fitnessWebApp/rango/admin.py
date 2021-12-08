from django.contrib import admin
from rango.models import Food, PostActivities, Profile_food, Profile_activity, PostFood, UserProfile, ActivityCategory, Activities

class Profile_foodAdmin(admin.ModelAdmin):
     list_display = ('person', 'calorie_consumed_day', 'date_today',)
     readonly_field = ('date',)

class Profile_activityAdmin(admin.ModelAdmin):
     list_display = ('person', 'calorie_burned', 'date_today',)
     readonly_field = ('date',)


class UserProfileAdmin(admin.ModelAdmin):
     list_display = ('user', 'weight', 'height', 'BMI',)

class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

class ActivitiesCategoryAdmin(admin.ModelAdmin):
    list_display = ('api_description', 'intensity_level', 'query_id', 'activity_category')

admin.site.register(Profile_food, Profile_foodAdmin)
admin.site.register(Profile_activity, Profile_activityAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Food)
admin.site.register(PostFood)
admin.site.register(PostActivities)
admin.site.register(ActivityCategory, ActivityCategoryAdmin)
admin.site.register(Activities, ActivitiesCategoryAdmin)

