from django.shortcuts import render, redirect, get_object_or_404
# these are tools from django:
# render = show a page
# redirect = go to another page
# get_object_or_404 = get data or show error if not found

from django.contrib.auth import authenticate, login
# authenticate = checks username/password
# login = logs user into the system

from django.contrib import messages
# this lets us show messages like errors or success on the page

from django.contrib.auth.decorators import login_required
# this makes sure user must be logged in to access a page

from .models import Team, Department, Person, Message
# this imports data models (tables) from models.py

from django.core.mail import send_mail
from django.conf import settings


def login_view(request):
    # this function runs when user opens login page

    if request.method == "POST":
        # this means user submitted the form

        username = request.POST.get("username")
        password = request.POST.get("password")
        # get username and password from form

        user = authenticate(request, username=username, password=password)
        # check if username and password are correct

        if user is not None:
            # if login is correct
            login(request, user)
            # log the user in
            return redirect("dashboard")
            # go to dashboard page

        else:
            # if login is wrong
            messages.error(request, "Invalid login details")
            # show error message

    return render(request, "login.html")
    # show login page


@login_required
def dashboard(request):
    # this page only works if user is logged in

    teams = Team.objects.select_related("department").order_by("-id")[:6]
    # get latest 6 teams from database

    departments = Department.objects.values_list("name", flat=True)
    department_list = ", ".join(sorted(set(departments)))
    # get department names and make a list

    context = {
        # context is data we send to the HTML page

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
        # fake notifications for display

        "meetings": [
            {"title": "Weekly Team Sync", "time": "10:00 AM"},
        ],
        # fake meetings
    }

    return render(request, "dashboard.html", context)
    # send data to dashboard page


@login_required
def teams_view(request):
    # shows all teams

    teams = Team.objects.select_related("department", "team_leader")
    # get all teams with related data

    return render(request, "teams.html", {
        "teams": teams
    })


@login_required
def team_detail(request, id):
    # shows one specific team

    team = get_object_or_404(
        Team.objects.select_related("department", "team_leader"),
        id=id
    )
    # get team by id

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
    # this shows inbox and sent messages

    current_user = request.user.person
    # temporary: first person in database is treated as logged user

    inbox = Message.objects.filter(
        receiver__team_leader=current_user
    ).select_related("sender", "receiver").order_by("-created_at")
    # get messages sent TO this user's team

    sent = Message.objects.filter(
        sender=current_user
    ).select_related("receiver").order_by("-created_at")
    # get messages sent BY this user

    unread_count = inbox.filter(is_read=False).count()
    # count unread messages

    return render(request, "messages.html", {
        "inbox": inbox,
        "sent": sent,
        "unread_count": unread_count,
    })


@login_required
def new_message(request):
    # this page creates a new message

    teams = Team.objects.all()
    # get all teams for dropdown

    if request.method == "POST":
        # user submitted form

        team_id = request.POST.get("team")
        subject = request.POST.get("subject")
        body = request.POST.get("body")

        if not subject or not body:
            # if fields are empty
            messages.error(request, "All fields required")
            return redirect("new_message")

        team = Team.objects.get(id=team_id)
        # find selected team

        sender = request.user.person
        # temporary sender

        Message.objects.create(
            sender=sender,
            receiver=team,
            subject=subject,
            body=body,
            is_read=False
        )
        # create and save message

        return redirect("messages")
        # go back to messages page

    return render(request, "new_message.html", {
        "teams": teams
    })


@login_required
def schedule_view(request):
    # shows schedule page
    return render(request, "schedule.html")


@login_required
def settings_view(request):
    # shows settings page

    if request.method == "POST":
        # if user clicks save

        from django.contrib import messages
        messages.success(request, "Settings saved successfully")
        # show success message

        return redirect("settings")

    return render(request, "settings.html")


def register_view(request):
    # shows register page
    return render(request, "register.html")


from django.core.mail import send_mail
from django.conf import settings


def reset_password_view(request):
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
    # handles new password page

    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            # if passwords don't match
            messages.error(request, "Passwords do not match")
            return redirect("new_password")

        messages.success(request, "Password updated successfully")
        # show success message

        return redirect("login")

    return render(request, "new_password.html")


@login_required
def message_detail(request, id):
    # shows one message

    message = get_object_or_404(
        Message.objects.select_related("sender", "receiver"),
        id=id
    )

    if not message.is_read:
        # if not read, mark as read
        message.is_read = True
        message.save()

    return render(request, "message_detail.html", {
        "message": message
    })


@login_required
def reply_message(request, id):
    # reply to a message

    original = get_object_or_404(Message, id=id)
    teams = Team.objects.all()

    if request.method == "POST":
        subject = "Re: " + original.subject
        body = request.POST.get("body")

        sender = request.user.person

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

    person = getattr(request.user, "person", None)

    return render(request, "profile.html", {
        "user": person,
        "email": request.user.email
    })


@login_required
def organisation_map_view(request):
    # shows organisation map page
    return render(request, "organisation_map.html")

"""This file controls the whole website.
Each function is a page.
It gets data from the database and sends it to HTML pages.
It also handles forms like login and messages."""

def test_email(request):
    try:
        send_mail(
            subject="TEST EMAIL",
            message="This is a test email from Django",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["alicanbozokluoglu@outlook.com"],  # your email
            fail_silently=False,
        )
        return HttpResponse("EMAIL SENT")

    except Exception as e:
        return HttpResponse(f"ERROR: {e}")