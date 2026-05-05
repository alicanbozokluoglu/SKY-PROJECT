from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    team = models.ForeignKey(
        "Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members"
    )

    teams = models.ManyToManyField(
        "Team",
        blank=True,
        related_name="extra_members"
    )

    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    photo = models.ImageField(upload_to="people/", null=True, blank=True)

    def __str__(self):
        return self.name


class UserSetting(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="settings_profile"
    )

    job_title = models.CharField(max_length=120, blank=True)

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    email_notifications = models.BooleanField(default=True)
    message_notifications = models.BooleanField(default=True)
    meeting_notifications = models.BooleanField(default=True)

    profile_visibility = models.CharField(
        max_length=50,
        choices=[
            ("public", "Public"),
            ("team_only", "Team Only"),
            ("private", "Private"),
        ],
        default="public"
    )

    default_view = models.CharField(
        max_length=50,
        choices=[
            ("dashboard", "Dashboard"),
            ("teams", "Teams"),
            ("messages", "Messages"),
            ("schedule", "Schedule"),
        ],
        default="dashboard"
    )

    theme = models.CharField(
        max_length=50,
        choices=[
            ("light", "Light"),
            ("dark", "Dark"),
            ("system", "System"),
        ],
        default="light"
    )

    background = models.CharField(
        max_length=20,
        choices=[
            ("default", "Default"),
            ("black", "Black"),
        ],
        default="default"
    )

    language = models.CharField(max_length=50, default="English UK")
    timezone = models.CharField(max_length=100, default="UTC")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} settings"


class Team(models.Model):
    name = models.CharField(max_length=100)

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    team_leader = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leading_teams"
    )

    description = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)

    members_count = models.PositiveIntegerField(default=0)
    repositories_count = models.PositiveIntegerField(default=0)
    active_projects_count = models.PositiveIntegerField(default=0)

    status = models.CharField(max_length=50, default="Active")

    github_link = models.URLField(blank=True)
    documentation_link = models.URLField(blank=True)
    calendar_link = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def total_members(self):
        primary_team_members = self.members.all()
        extra_team_members = self.extra_members.all()

        member_ids = set(primary_team_members.values_list("id", flat=True))
        member_ids.update(extra_team_members.values_list("id", flat=True))

        if self.team_leader:
            member_ids.add(self.team_leader.id)

        return len(member_ids)

    def total_repositories(self):
        return self.repositories.count()

    def total_dependencies(self):
        return self.dependencies_from.count()

    def __str__(self):
        return self.name

    def clean(self):
        member_total = self.total_members()

        if member_total < 5:
            raise ValidationError("Each team must have at least 5 members.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Repository(models.Model):
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="repositories"
    )

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    technology = models.CharField(max_length=100, blank=True)
    last_updated = models.DateField(null=True, blank=True)
    url = models.URLField(blank=True)

    class Meta:
        verbose_name_plural = "Repositories"

    def __str__(self):
        return self.name


class TeamDependency(models.Model):
    source_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="dependencies_from"
    )

    target_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="dependencies_to"
    )

    description = models.TextField(blank=True)
    dependency_type = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=50, default="Active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Team Dependencies"

    def __str__(self):
        return f"{self.source_team.name} -> {self.target_team.name}"


class Message(models.Model):
    sender = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )

    receiver = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="received_messages"
    )

    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject


class Activity(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    related_team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Activities"

    def __str__(self):
        return self.title


class ScheduleEvent(models.Model):
    title = models.CharField(max_length=200)

    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_schedule_events"
    )

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    platform = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.title


class UserActivity(models.Model):
    ACTION_CHOICES = [
        ("team_visit", "Team Visit"),
        ("message_sent", "Message Sent"),
        ("message_reply", "Message Reply"),
        ("schedule_created", "Schedule Created"),
        ("settings_updated", "Settings Updated"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="personal_activities"
    )

    action_type = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        default="other"
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    related_team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_activities"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "User Activities"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title}"