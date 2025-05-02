# Copyright 2013-2020 Stefan Hajnoczi <stefanha@gmail.com>

from django.contrib import admin
from .models import RecordedJam

class RecordedJamAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'owner_name', 'users_list', 'duration')
    raw_id_fields = ('owner', 'users')
    search_fields = ('owner__username', 'users__username')

    def owner_name(self, obj):
        owner = obj.owner
        return owner.username if owner is not None else ''
    owner_name.short_description = 'Owner'

    def users_list(self, obj):
        return ', '.join(u.username for u in obj.users.all())
    users_list.short_description = 'Users'

admin.site.register(RecordedJam, RecordedJamAdmin)
