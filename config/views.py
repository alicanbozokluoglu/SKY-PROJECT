from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required

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


@login_required
def dashboard(request):

    # MOCK DATA (replace later with models)
    teams = [
        {
            "name": "Backend Team",
            "department": "Engineering",
            "manager_name": "John Smith",
            "role": "Manager",
            "manager_image": "https://via.placeholder.com/35"
        },
        {
            "name": "Frontend Team",
            "department": "Engineering",
            "manager_name": "Sarah Johnson",
            "role": "Manager",
            "manager_image": "https://via.placeholder.com/35"
        },
        {
            "name": "DevOps Team",
            "department": "IT Operations",
            "manager_name": "James Brown",
            "role": "Manager",
            "manager_image": "https://via.placeholder.com/35"
        }
    ]

    notifications = [
        {"message": "New team created", "time": "2 hours ago"},
        {"message": "Team updated", "time": "1 day ago"},
        {"message": "New member added", "time": "2 days ago"},
    ]

    meetings = [
        {"title": "Backend Team Sync", "time": "10:00 AM - 11:00 AM"}
    ]

    context = {
        "teams": teams,
        "notifications": notifications,
        "meetings": meetings,

        "total_teams": 12,
        "teams_this_month": "+2",

        "total_departments": 3,
        "department_list": "Engineering, Product, IT",

        "total_members": 65,
        "members_this_month": "+15",
    }

    return render(request, "dashboard.html", context)

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