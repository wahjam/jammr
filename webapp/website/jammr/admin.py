# Copyright 2013-2020 Stefan Hajnoczi <stefanha@gmail.com>

from django.contrib import admin
from .models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'user__email')
    list_display = ('user', 'subscription')
    raw_id_fields = ('user',)

admin.site.register(UserProfile, UserProfileAdmin)
