from django.contrib import admin
from django.urls import path
from dashboard import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),

    path("teams/", views.teams_view, name="teams"),
    path("departments/", views.departments_view, name="departments"),

    path("admin/", admin.site.urls),
    path("register/", views.register_view, name="register"),
    path("reset/", views.reset_password_view, name="reset"),
    path("new-password/", views.new_password_view, name="new_password"),
    path("team/<int:id>/", views.team_detail, name="team_detail"),
]
