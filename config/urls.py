from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from dashboard import views


urlpatterns = [
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),

    path("admin-team-management/", views.admin_team_management, name="admin_team_management"),
    path("admin-department-management/", views.admin_department_management, name="admin_department_management"),
    path("admin-user-access/", views.admin_user_access, name="admin_user_access"),
    path("admin-person-management/", views.admin_person_management, name="admin_person_management"),

    path("search/", views.global_search, name="global_search"),

    path("teams/", views.teams_view, name="teams"),
    path("team/<int:id>/", views.team_detail, name="team_detail"),

    path("departments/", views.departments_view, name="departments"),

    path("people/<int:id>/", views.person_profile, name="person_profile"),

    path("settings/", views.settings_view, name="settings"),
    path("register/", views.register_view, name="register"),

    path("messages/", views.messages_view, name="messages"),
    path("messages/new/", views.new_message, name="new_message"),
    path("messages/<int:id>/", views.message_detail, name="message_detail"),
    path("messages/<int:id>/reply/", views.reply_message, name="reply_message"),

    path("profile/", views.profile_view, name="profile"),
    path("schedule/", views.schedule_view, name="schedule"),
    path("organisation-map/", views.organisation_map_view, name="organisation_map"),

    path("admin/", admin.site.urls),

    path(
        "reset/",
        auth_views.PasswordResetView.as_view(
            template_name="password_reset_form.html",
            email_template_name="password_reset_email.html",
            subject_template_name="password_reset_subject.txt",
            success_url="/reset/done/",
        ),
        name="password_reset",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html",
            success_url="/reset/complete/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)