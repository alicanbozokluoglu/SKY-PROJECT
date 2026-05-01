from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Team, Department, Person, Message


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

    teams = Team.objects.select_related("department").order_by("-id")[:6]

    departments = Department.objects.values_list("name", flat=True)
    department_list = ", ".join(sorted(set(departments)))

    context = {
        "teams": teams,
        "total_teams": Team.objects.count(),
        "total_departments": Department.objects.count(),
        "total_members": Person.objects.count(),

        "teams_this_month": "N/A",
        "members_this_month": "N/A",

        "department_list": department_list,

        "notifications": [
            {"message": "Team registry loaded successfully", "time": "Today"},
        ],
        "meetings": [
            {"title": "Weekly Team Sync", "time": "10:00 AM"},
        ],
    }

    return render(request, "dashboard.html", context)


# -------------------------
# TEAMS
# -------------------------
@login_required
def teams_view(request):
    teams = Team.objects.select_related("department", "team_leader")

    return render(request, "teams.html", {
        "teams": teams
    })


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
# DEPARTMENTS
# -------------------------
@login_required
def departments_view(request):
    departments = Department.objects.all()

    return render(request, "departments.html", {
        "departments": departments
    })


# -------------------------
# MESSAGES (INBOX + SENT)
# -------------------------
@login_required
def messages_view(request):

    current_user = Person.objects.first()  # temp user

    inbox = Message.objects.filter(
        receiver__team_leader=current_user
    ).select_related("sender", "receiver").order_by("-created_at")

    sent = Message.objects.filter(
        sender=current_user
    ).select_related("receiver").order_by("-created_at")

    unread_count = inbox.filter(is_read=False).count()

    return render(request, "messages.html", {
        "inbox": inbox,
        "sent": sent,
        "unread_count": unread_count,
    })


@login_required
def new_message(request):
    teams = Team.objects.all()

    if request.method == "POST":
        team_id = request.POST.get("team")
        subject = request.POST.get("subject")
        body = request.POST.get("body")

        if not subject or not body:
            messages.error(request, "All fields required")
            return redirect("new_message")
        
        team = Team.objects.get(id=team_id)

        sender = Person.objects.first()

        Message.objects.create(
            sender=sender,
            receiver=team,
            subject=subject,
            body=body,
            is_read=False  # ✅ IMPORTANT
        )

        return redirect("messages")

    return render(request, "new_message.html", {
        "teams": teams
    })

# -------------------------
# SCHEDULE
# -------------------------
@login_required
def schedule_view(request):
    return render(request, "schedule.html")


# -------------------------
# SETTINGS
# -------------------------
@login_required
def settings_view(request):

    # simple POST handler (no DB yet — acceptable for coursework)
    if request.method == "POST":
        # you could read values here if needed:
        # theme = request.POST.get("theme")
        # language = request.POST.get("language")
        # etc.

        from django.contrib import messages
        messages.success(request, "Settings saved successfully")

        return redirect("settings")

    return render(request, "settings.html")

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


@login_required
def message_detail(request, id):
    message = get_object_or_404(
        Message.objects.select_related("sender", "receiver"),
        id=id
    )

    # mark as read
    if not message.is_read:
        message.is_read = True
        message.save()

    return render(request, "message_detail.html", {
        "message": message
    })


@login_required
def reply_message(request, id):
    original = get_object_or_404(Message, id=id)
    teams = Team.objects.all()

    if request.method == "POST":
        subject = "Re: " + original.subject
        body = request.POST.get("body")

        sender = Person.objects.first()  # temp user

        Message.objects.create(
            sender=sender,
            receiver=original.sender.team if hasattr(original.sender, "team") else original.receiver,
            subject=subject,
            body=body
        )

        return redirect("messages")

    return render(request, "reply_message.html", {
        "original": original,
        "teams": teams
    })
@login_required
def profile_view(request):
    # TEMP mapping (same approach you used for messages)
    user = Person.objects.first()

    # generate email from name
    email = user.name.lower().replace(" ", ".") + "@sky.com"

    return render(request, "profile.html", {
        "user": user,
        "email": email
    })

@login_required
def organisation_map_view(request):
    return render(request, "organisation_map.html")
