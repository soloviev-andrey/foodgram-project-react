from django.contrib import admin

from users.models import CustomUser, Subscrime

admin.site.empty_value_display = 'Не задано'


class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
    )
    search_fields = ('username',)
    list_filter = (
        'email',
        'username'
    )
    list_display_links = ('username',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Subscrime)
