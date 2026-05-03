from django.shortcuts import render, redirect, get_object_or_404
# render = show page
# redirect = go to another page
# get_object_or_404 = get data or show error if not found

from django.contrib.auth import authenticate, login
# authenticate = check username and password
# login = log user into system

from django.contrib import messages
# this shows messages like errors or success

from django.contrib.auth.decorators import login_required
# user must be logged in to use page

from .models import Team, Department, Person, Message
# these are database tables

from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse

from django.db.models import Q
# this helps search in many places


def login_view(request):
    # this page lets user log in

    if request.method == "POST":
        # user sent form

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # correct login
            login(request, user)
            return redirect("dashboard")

        else:
            # wrong login
            messages.error(request, "Invalid login details")

    return render(request, "login.html")


@login_required
def dashboard(request):
    # this shows main dashboard page

    teams = Team.objects.select_related("department").order_by("-id")[:6]
    # get last 6 teams

    departments = Department.objects.values_list("name", flat=True)
    department_list = ", ".join(sorted(set(departments)))
    # make list of department names

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


def teams_view(request):
    # this page shows all teams and also search

    query = request.GET.get("q")
    # this gets what user typed

    teams = Team.objects.select_related("department", "team_leader")

    if query:
        # if user typed something

        teams = teams.filter(
            Q(name__icontains=query) |
            Q(department__name__icontains=query) |
            Q(team_leader__name__icontains=query)
        )

        # this means search in:
        # team name
        # department name
        # team leader name

    return render(request, "teams.html", {
        "teams": teams
    })


@login_required
def team_detail(request, id):
    # this shows one team

    team = get_object_or_404(
        Team.objects.select_related("department", "team_leader"),
        id=id
    )

    return render(request, "team_detail.html", {
        "team": team
    })


@login_required
def departments_view(request):
    # shows all departments

    departments = Department.objects.all()

    return render(request, "departments.html", {
        "departments": departments
    })


@login_required
def messages_view(request):
    # shows inbox and sent messages

    person = getattr(request.user, "person", None)
    # get person safely (avoid crash)

    if not person:
        return redirect("login")

    inbox = Message.objects.filter(
        receiver__team_leader=person
    ).select_related("sender", "receiver").order_by("-created_at")

    sent = Message.objects.filter(
        sender=person
    ).select_related("receiver").order_by("-created_at")

    unread_count = inbox.filter(is_read=False).count()

    return render(request, "messages.html", {
        "inbox": inbox,
        "sent": sent,
        "unread_count": unread_count,
    })


@login_required
def new_message(request):
    # create new message

    teams = Team.objects.all()

    if request.method == "POST":

        team_id = request.POST.get("team")
        subject = request.POST.get("subject")
        body = request.POST.get("body")

        if not subject or not body:
            messages.error(request, "All fields required")
            return redirect("new_message")

        team = Team.objects.get(id=team_id)

        person = getattr(request.user, "person", None)

        Message.objects.create(
            sender=person,
            receiver=team,
            subject=subject,
            body=body,
            is_read=False
        )

        return redirect("messages")

    return render(request, "new_message.html", {
        "teams": teams
    })


@login_required
def schedule_view(request):
    # shows schedule page
    return render(request, "schedule.html")


@login_required
def settings_view(request):
    # settings page

    if request.method == "POST":
        messages.success(request, "Settings saved successfully")
        return redirect("settings")

    return render(request, "settings.html")


def register_view(request):
    # register page
    return render(request, "register.html")


def reset_password_view(request):
    # send reset email

    if request.method == "POST":
        email = request.POST.get("email")

        if not email:
            messages.error(request, "Please enter your email")
            return redirect("reset")

        try:
            send_mail(
                subject="Password Reset - SKY",
                message="Click this link:\nhttp://127.0.0.1:8000/new-password/",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            print("EMAIL SENT SUCCESSFULLY")

        except Exception as e:
            print("EMAIL ERROR:", e)

        messages.success(request, "Reset link sent to your email")
        return redirect("login")

    return render(request, "reset.html")


def new_password_view(request):
    # set new password

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
    # open one message

    message = get_object_or_404(
        Message.objects.select_related("sender", "receiver"),
        id=id
    )

    if not message.is_read:
        message.is_read = True
        message.save()

    return render(request, "message_detail.html", {
        "message": message
    })


@login_required
def reply_message(request, id):
    # reply to message

    original = get_object_or_404(Message, id=id)
    teams = Team.objects.all()

    if request.method == "POST":
        subject = "Re: " + original.subject
        body = request.POST.get("body")

        person = getattr(request.user, "person", None)

        Message.objects.create(
            sender=person,
            receiver=original.receiver,
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
    # show user profile

    person = getattr(request.user, "person", None)

    return render(request, "profile.html", {
        "user": person,
        "email": request.user.email
    })


@login_required
def organisation_map_view(request):
    # show organisation map
    return render(request, "organisation_map.html")


def test_email(request):
    # test sending email

    try:
        send_mail(
            subject="TEST EMAIL",
            message="This is a test email from Django",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["alicanbozokluoglu@outlook.com"],
            fail_silently=False,
        )
        return HttpResponse("EMAIL SENT")

    except Exception as e:
        return HttpResponse(f"ERROR: {e}")


"""
this file controls the website.
each function is a page.
it gets data from database and shows it.
it also handles login, messages, and email.
"""