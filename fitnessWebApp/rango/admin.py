from django.contrib import admin
from rango.models import Food, Profile, PostFood, Category, UserProfile, Video

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('person', 'calorie_consumed_day', 'date_today')
    readonly_field = ('date',)

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('name',)}

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'weight', 'height', 'BMI',)

admin.site.register(Profile, ProfileAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Food)
admin.site.register(PostFood)
admin.site.register(Video)

