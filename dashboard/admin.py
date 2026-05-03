from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .models import (
    Department,
    Team,
    Person,
    UserSetting,
    Repository,
    TeamDependency,
    Message,
    Activity,
    ScheduleEvent,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "email", "team", "phone", "user")
    list_filter = ("team",)
    search_fields = ("name", "email", "role", "team__name")


@admin.register(UserSetting)
class UserSettingAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "job_title",
        "department",
        "email_notifications",
        "message_notifications",
        "meeting_notifications",
        "profile_visibility",
        "default_view",
        "theme",
        "language",
        "timezone",
        "updated_at",
    )
    list_filter = ("department", "profile_visibility", "default_view", "theme")
    search_fields = ("user__username", "user__email", "job_title", "language", "timezone")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "department",
        "team_leader",
        "real_members_total",
        "real_repositories_total",
        "real_dependencies_total",
        "active_projects_count",
        "status",
    )
    list_filter = ("department", "status")
    search_fields = ("name", "team_leader__name", "department__name")

    def real_members_total(self, obj):
        return obj.total_members()

    def real_repositories_total(self, obj):
        return obj.repositories.count()

    def real_dependencies_total(self, obj):
        return obj.dependencies_from.count()


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ("name", "team", "technology", "last_updated", "url")
    list_filter = ("team", "technology")
    search_fields = ("name", "team__name", "technology")


@admin.register(TeamDependency)
class TeamDependencyAdmin(admin.ModelAdmin):
    list_display = ("source_team", "target_team", "dependency_type", "status", "created_at")
    list_filter = ("source_team", "target_team", "status")
    search_fields = (
        "source_team__name",
        "target_team__name",
        "dependency_type",
        "description",
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "sender", "receiver", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("subject", "sender__name", "receiver__name")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "related_team", "created_at")
    search_fields = ("title", "description", "related_team__name")
    list_filter = ("created_at",)


@admin.register(ScheduleEvent)
class ScheduleEventAdmin(admin.ModelAdmin):
    list_display = ("title", "team", "date", "start_time", "end_time", "platform")
    list_filter = ("date", "team")
    search_fields = ("title", "team__name", "platform")


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff", "is_active")