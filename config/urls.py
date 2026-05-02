from django.contrib import admin
# this allows access to the admin panel

from django.urls import path
# this lets us define website URLs (links)

from dashboard import views
# this imports all functions from views.py

from django.contrib.auth import views as auth_views

urlpatterns = [
    # this is the main list of all website routes (pages)


    path("", views.login_view, name="login"),
    # when user goes to the main URL (home page),
    # it shows the login page


    path("dashboard/", views.dashboard, name="dashboard"),
    # this opens the dashboard page


    path("teams/", views.teams_view, name="teams"),
    # shows all teams

    path("team/<int:id>/", views.team_detail, name="team_detail"),
    # shows one specific team
    # <int:id> means it takes a number from the URL
    # example: /team/3/


    path("departments/", views.departments_view, name="departments"),
    # shows departments page


    path("settings/", views.settings_view, name="settings"),
    # opens settings page


    path("admin/", admin.site.urls),
    # django admin panel (for developers)


    path("register/", views.register_view, name="register"),
    # register page


    path("new-password/", views.new_password_view, name="new_password"),
    # create new password page


    path("messages/<int:id>/", views.message_detail, name="message_detail"),
    # open one message

    path("messages/<int:id>/reply/", views.reply_message, name="reply_message"),
    # reply to a message

    path("messages/", views.messages_view, name="messages"),
    # messages inbox page

    path("messages/new/", views.new_message, name="new_message"),
    # create a new message


    path("profile/", views.profile_view, name="profile"),
    # user profile page

    path("schedule/", views.schedule_view, name="schedule"),
    # schedule/calendar page

    path("organisation-map/", views.organisation_map_view, name="organisation_map"),
    # organisation map page
    path('reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

"""This file connects URLs to pages.
When the user clicks a link, Django uses this file to decide which function to run and which page to show."""