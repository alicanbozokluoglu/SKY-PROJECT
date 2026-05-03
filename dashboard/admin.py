from django.contrib import admin
# this lets us use Django admin panel (the control dashboard)

from .models import Department, Team, Person, Message
# this imports our database tables from "models.py"


# this section controls how PERSON appears in admin panel
@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):

    # this shows these columns in admin table
    list_display = ("name", "user")

    # this adds a search box to search by name
    search_fields = ("name",)


# this section controls how TEAM appears in admin panel
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):

    # shows these columns in admin
    list_display = ("name", "department", "team_leader")

    # this adds a filter (on the right side) to filter by department
    list_filter = ("department",)


# this section controls how DEPARTMENT appears in admin panel
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):

    # shows department name
    list_display = ("name",)


# this section controls how MESSAGE appears in admin panel
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    # shows these columns in admin
    list_display = ("subject", "sender", "receiver", "is_read", "created_at")


# this part edits the default Django User (login users)
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin


# this removes the default User view (optional, just cleaner)
admin.site.unregister(User)


# this re-registers User with custom settings
@admin.register(User)
class CustomUserAdmin(UserAdmin):

    # this controls what columns you see in admin for users
    list_display = ("username", "email", "is_staff", "is_active")

#This file controls how your data looks in the admin panel