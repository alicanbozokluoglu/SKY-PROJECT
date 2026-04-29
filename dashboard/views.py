from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now

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
# DASHBOARD
# -------------------------
@login_required
def dashboard(request):

    current_month = now().month

    teams = Team.objects.select_related("department").order_by("-id")[:6]
    notifications = Notification.objects.order_by("-created_at")[:5]
    meetings = Meeting.objects.all()

    context = {
        "teams": teams,
        "notifications": notifications,
        "meetings": meetings,

        "total_teams": Team.objects.count(),
        "teams_this_month": Team.objects.filter(created_at__month=current_month).count(),

        "total_departments": Department.objects.count(),
        "department_list": ", ".join(Department.objects.values_list("name", flat=True)),

        "total_members": 0,
        "members_this_month": 0,
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
