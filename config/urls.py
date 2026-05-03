from django.contrib import admin
# this lets us use the Django admin panel (a special page for managing data)

from django.urls import path
# this is used to create website links (URLs)

from dashboard import views
# this imports all the functions from "views.py"
# each function is a page (like dashboard, teams, etc.)

from django.contrib.auth import views as auth_views
# this imports ready-made login and password reset tools from Django


# this list connects URL links to functions (pages)
urlpatterns = [

    # when user goes to the main page ("/")
    # it will show the login page
    path("", views.login_view, name="login"),


    # this opens the dashboard page
    path("dashboard/", views.dashboard, name="dashboard"),


    # this shows all teams
    path("teams/", views.teams_view, name="teams"),


    # this shows ONE team
    # <int:id> means Django takes a number from the URL
    # example: /team/3/ → shows team with id=3
    path("team/<int:id>/", views.team_detail, name="team_detail"),


    # this shows all departments
    path("departments/", views.departments_view, name="departments"),


    # this opens the settings page
    path("settings/", views.settings_view, name="settings"),


    # this opens Django admin panel (for managing data like users)
    path("admin/", admin.site.urls),


    # this opens the register page
    path("register/", views.register_view, name="register"),


    # this opens page where user creates new password
    path("new-password/", views.new_password_view, name="new_password"),


    # this shows ONE message
    path("messages/<int:id>/", views.message_detail, name="message_detail"),


    # this lets user reply to a message
    path("messages/<int:id>/reply/", views.reply_message, name="reply_message"),


    # this shows all messages (inbox + sent)
    path("messages/", views.messages_view, name="messages"),


    # this lets user create a new message
    path("messages/new/", views.new_message, name="new_message"),


    # this shows the user profile page
    path("profile/", views.profile_view, name="profile"),


    # this shows the schedule page
    path("schedule/", views.schedule_view, name="schedule"),


    # this shows organisation map page
    path("organisation-map/", views.organisation_map_view, name="organisation_map"),



    # this page shows the form where user enters email
    # it uses a template file: "password_reset_form.html"
    path('reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset_form.html'
    ), name='password_reset'),


    # after user submits email, they see a "check your email" page
    path('reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'
    ), name='password_reset_done'),


    # this is the special link sent in email
    # it contains a unique id and token (security)
    # example: /reset/abc123/token123/
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html'
    ), name='password_reset_confirm'),


    # after user changes password, they see success page
    path('reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ), name='password_reset_complete'),
]

"""This file connects URLs to pages.
When the user clicks a link, Django uses this file to decide which function to run and which page to show."""