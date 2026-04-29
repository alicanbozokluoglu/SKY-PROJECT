from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Team, Department, Notification, Meeting


# -------------------------
# AUTH: LOGIN
# -------------------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid login details")

    return render(request, "login.html")


# -------------------------
# DASHBOARD (DATABASE-DRIVEN)
# -------------------------
@login_required
def dashboard(request):

    teams = Team.objects.all()
    departments = Department.objects.all()
    notifications = Notification.objects.all()
    meetings = Meeting.objects.all()

    context = {
        "teams": teams,
        "notifications": notifications,
        "meetings": meetings,

        "total_teams": teams.count(),
        "teams_this_month": "+2",  # static placeholder (acceptable for CWK)

        "total_departments": departments.count(),
        "department_list": ", ".join([d.name for d in departments]),

        "total_members": 65,  # placeholder (no user model implemented yet)
        "members_this_month": "+15",
    }

    return render(request, "dashboard.html", context)


# -------------------------
# SIMPLE AUTH PAGES
# -------------------------
def register_view(request):
    return render(request, "register.html")


def reset_password_view(request):
    return render(request, "reset.html")


def new_password_view(request):
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("new_password")

        messages.success(request, "Password updated successfully")
        return redirect("login")

    return render(request, "new_password.html")
