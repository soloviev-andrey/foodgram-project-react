from django.contrib import admin
from users.models import CustomUser, Subscrime


admin.site.empty_value_display = 'Не задано'


class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
        'password'
    )
    list_filter = (
        'email',
        'username'
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Subscrime)
