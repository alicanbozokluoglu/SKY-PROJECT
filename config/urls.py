from django.contrib import admin
from django.urls import path
from dashboard import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),

    path("teams/", views.teams_view, name="teams"),
    path("team/<int:id>/", views.team_detail, name="team_detail"),
    path("departments/", views.departments_view, name="departments"),

    path("messages/", views.messages_view, name="messages"),
    path("messages/new/", views.new_message, name="new_message"),

    path("schedule/", views.schedule_view, name="schedule"),
    path("settings/", views.settings_view, name="settings"),

    path("admin/", admin.site.urls),

    path("register/", views.register_view, name="register"),
    path("reset/", views.reset_password_view, name="reset"),
    path("new-password/", views.new_password_view, name="new_password"),
    path("messages/<int:id>/", views.message_detail, name="message_detail"),
    path("messages/<int:id>/reply/", views.reply_message, name="reply_message"),
    path("messages/", views.messages_view, name="messages"),
    path("messages/new/", views.new_message, name="new_message"),
    path("profile/", views.profile_view, name="profile"),
    path("settings/", views.settings_view, name="settings"),
    path("schedule/", views.schedule_view, name="schedule"),
]