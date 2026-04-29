from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Team, Department, Person


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
# DASHBOARD (CLEAN VERSION)
# -------------------------
@login_required
def dashboard(request):

    teams = Team.objects.select_related("department").order_by("-id")[:6]

    departments = Department.objects.values_list("name", flat=True)
    department_list = ", ".join(sorted(set(departments)))

    notifications = [
        {"message": "Team registry loaded successfully", "time": "Today"},
    ]

    meetings = [
        {"title": "Weekly Team Sync", "time": "10:00 AM"},
    ]

    context = {
        "teams": teams,

        "total_teams": Team.objects.count(),
        "total_departments": Department.objects.count(),
        "total_members": Person.objects.count(),

        "teams_this_month": "N/A",
        "members_this_month": "N/A",

        "department_list": department_list,
        "notifications": notifications,
        "meetings": meetings,
    }

    return render(request, "dashboard.html", context)


# -------------------------
# TEAM DETAIL
# -------------------------
@login_required
def team_detail(request, id):
    team = get_object_or_404(
        Team.objects.select_related("department", "team_leader"),
        id=id
    )

    return render(request, "team_detail.html", {
        "team": team
    })


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