from django.contrib import admin
from .models import Department, Team, Person, Message


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "user")
    search_fields = ("name",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "team_leader")
    list_filter = ("department",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "sender", "receiver", "is_read", "created_at")

from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

admin.site.unregister(User)  # optional but cleaner

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff", "is_active")   