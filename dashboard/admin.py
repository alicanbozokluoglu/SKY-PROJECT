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
    UserActivity,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "email", "team", "show_teams", "phone", "user")
    list_filter = ("team", "teams")
    search_fields = ("name", "email", "role", "team__name", "teams__name")
    filter_horizontal = ("teams",)

    def show_teams(self, person):
        return ", ".join(person.teams.values_list("name", flat=True))

    show_teams.short_description = "Teams"


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
        "background",
        "language",
        "timezone",
        "updated_at",
    )
    list_filter = (
        "department",
        "profile_visibility",
        "default_view",
        "theme",
        "background",
    )
    search_fields = (
        "user__username",
        "user__email",
        "job_title",
        "language",
        "timezone",
    )


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "department",
        "team_leader",
        "show_member_count",
        "show_repository_count",
        "show_dependency_count",
        "active_projects_count",
        "status",
    )
    list_filter = ("department", "status")
    search_fields = ("name", "team_leader__name", "department__name")

    def show_member_count(self, team):
        return team.total_members()

    def show_repository_count(self, team):
        return team.repositories.count()

    def show_dependency_count(self, team):
        return team.dependencies_from.count()

    show_member_count.short_description = "Members"
    show_repository_count.short_description = "Repositories"
    show_dependency_count.short_description = "Dependencies"


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ("name", "team", "technology", "last_updated", "url")
    list_filter = ("team", "technology")
    search_fields = ("name", "team__name", "technology")


@admin.register(TeamDependency)
class TeamDependencyAdmin(admin.ModelAdmin):
    list_display = (
        "source_team",
        "target_team",
        "dependency_type",
        "status",
        "created_at",
    )
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
    list_display = (
        "title",
        "team",
        "created_by",
        "date",
        "start_time",
        "end_time",
        "platform",
    )
    list_filter = ("date", "team", "created_by")
    search_fields = (
        "title",
        "team__name",
        "platform",
        "created_by__username",
        "created_by__email",
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "action_type",
        "title",
        "related_team",
        "created_at",
    )
    list_filter = (
        "action_type",
        "related_team",
        "created_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "title",
        "description",
        "related_team__name",
    )
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff", "is_active")