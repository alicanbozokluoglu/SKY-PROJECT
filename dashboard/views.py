from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse

from .models import (
    Team,
    Department,
    Person,
    UserSetting,
    Repository,
    TeamDependency,
    Message,
    Activity,
    ScheduleEvent,
)


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if role == "admin":
                return redirect("admin_dashboard")

            return redirect("dashboard")

        messages.error(request, "Invalid login details")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


def register_view(request):
    if request.method == "POST":
        fullname = request.POST.get("fullname")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not fullname or not username or not email or not password or not confirm_password:
            messages.error(request, "All fields are required.")
            return redirect("register")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.first_name = fullname
        user.save()

        Person.objects.create(
            user=user,
            name=fullname,
            email=email
        )

        UserSetting.objects.get_or_create(user=user)

        messages.success(request, "Account created successfully. You can now log in.")
        return redirect("login")

    return render(request, "register.html")


@login_required
def dashboard(request):
    teams = Team.objects.select_related("department", "team_leader").order_by("-created_at")[:6]
    activities = Activity.objects.select_related("related_team").order_by("-created_at")[:5]
    meetings = ScheduleEvent.objects.select_related("team").order_by("date", "start_time")[:5]

    context = {
        "teams": teams,
        "total_teams": Team.objects.count(),
        "total_departments": Department.objects.count(),
        "total_members": Person.objects.count(),
        "total_messages": Message.objects.count(),
        "total_meetings": ScheduleEvent.objects.count(),
        "activities": activities,
        "meetings": meetings,
    }

    return render(request, "dashboard.html", context)


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access the admin dashboard.")
        return redirect("dashboard")

    teams = Team.objects.select_related("department", "team_leader").order_by("name")
    departments = Department.objects.all().order_by("name")
    people = Person.objects.select_related("team").order_by("name")

    context = {
        "teams": teams,
        "departments": departments,
        "people": people,
        "total_teams": Team.objects.count(),
        "total_departments": Department.objects.count(),
        "total_members": Person.objects.count(),
        "total_messages": Message.objects.count(),
        "total_meetings": ScheduleEvent.objects.count(),
        "latest_teams": Team.objects.select_related("department", "team_leader").order_by("-created_at")[:8],
        "latest_messages": Message.objects.select_related("sender", "receiver").order_by("-created_at")[:6],
        "latest_events": ScheduleEvent.objects.select_related("team").order_by("date", "start_time")[:6],
        "activities": Activity.objects.select_related("related_team").order_by("-created_at")[:8],
    }

    return render(request, "admin_dashboard.html", context)


@login_required
def admin_team_management(request):
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access team management.")
        return redirect("dashboard")

    departments = Department.objects.all().order_by("name")
    people = Person.objects.all().order_by("name")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_team":
            name = request.POST.get("name", "").strip()
            department_id = request.POST.get("department")
            team_leader_id = request.POST.get("team_leader")
            status = request.POST.get("status", "Active").strip()
            location = request.POST.get("location", "").strip()
            description = request.POST.get("description", "").strip()
            active_projects_count = request.POST.get("active_projects_count") or 0
            github_link = request.POST.get("github_link", "").strip()
            documentation_link = request.POST.get("documentation_link", "").strip()
            calendar_link = request.POST.get("calendar_link", "").strip()

            if not name:
                messages.error(request, "Team name is required.")
                return redirect("admin_team_management")

            department = Department.objects.filter(id=department_id).first() if department_id else None
            team_leader = Person.objects.filter(id=team_leader_id).first() if team_leader_id else None

            team = Team.objects.create(
                name=name,
                department=department,
                team_leader=team_leader,
                status=status or "Active",
                location=location,
                description=description,
                active_projects_count=active_projects_count,
                github_link=github_link,
                documentation_link=documentation_link,
                calendar_link=calendar_link,
            )

            Activity.objects.create(
                title="Team created",
                description=f"{team.name} was created from Team Management.",
                related_team=team,
            )

            messages.success(request, "Team created successfully.")
            return redirect("admin_team_management")

        if action == "update_team":
            team_id = request.POST.get("team_id")
            team = get_object_or_404(Team, id=team_id)

            name = request.POST.get("name", "").strip()

            if not name:
                messages.error(request, "Team name is required.")
                return redirect("admin_team_management")

            team.name = name
            team.department = Department.objects.filter(id=request.POST.get("department")).first() if request.POST.get("department") else None
            team.team_leader = Person.objects.filter(id=request.POST.get("team_leader")).first() if request.POST.get("team_leader") else None
            team.status = request.POST.get("status", "Active").strip() or "Active"
            team.location = request.POST.get("location", "").strip()
            team.description = request.POST.get("description", "").strip()
            team.active_projects_count = request.POST.get("active_projects_count") or 0
            team.github_link = request.POST.get("github_link", "").strip()
            team.documentation_link = request.POST.get("documentation_link", "").strip()
            team.calendar_link = request.POST.get("calendar_link", "").strip()
            team.save()

            Activity.objects.create(
                title="Team updated",
                description=f"{team.name} was updated from Team Management.",
                related_team=team,
            )

            messages.success(request, "Team updated successfully.")
            return redirect("admin_team_management")

        if action == "delete_team":
            team_id = request.POST.get("team_id")
            team = get_object_or_404(Team, id=team_id)
            team_name = team.name
            team.delete()

            Activity.objects.create(
                title="Team deleted",
                description=f"{team_name} was deleted from Team Management.",
                related_team=None,
            )

            messages.success(request, "Team deleted successfully.")
            return redirect("admin_team_management")

    teams = Team.objects.select_related("department", "team_leader").order_by("name")

    search = request.GET.get("search", "").strip()
    department = request.GET.get("department", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        teams = teams.filter(name__icontains=search)

    if department:
        teams = teams.filter(department_id=department)

    if status:
        teams = teams.filter(status__iexact=status)

    context = {
        "teams": teams,
        "departments": departments,
        "people": people,
        "search": search,
        "selected_department": department,
        "selected_status": status,
        "total_teams": Team.objects.count(),
        "total_departments": Department.objects.count(),
        "total_members": Person.objects.count(),
        "total_repositories": Repository.objects.count(),
    }

    return render(request, "admin_team_management.html", context)


@login_required
def admin_user_access(request):
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access user access management.")
        return redirect("dashboard")

    users = User.objects.all().order_by("username")

    search = request.GET.get("search", "").strip()
    role = request.GET.get("role", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        users = users.filter(username__icontains=search)

    if role == "admin":
        users = users.filter(is_staff=True)

    if role == "user":
        users = users.filter(is_staff=False)

    if status == "active":
        users = users.filter(is_active=True)

    if status == "inactive":
        users = users.filter(is_active=False)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_user":
            username = request.POST.get("username", "").strip()
            email = request.POST.get("email", "").strip()
            password = request.POST.get("password", "").strip()
            full_name = request.POST.get("full_name", "").strip()
            is_staff = bool(request.POST.get("is_staff"))
            is_active = bool(request.POST.get("is_active"))

            if not username or not password:
                messages.error(request, "Username and password are required.")
                return redirect("admin_user_access")

            if User.objects.filter(username=username).exists():
                messages.error(request, "This username already exists.")
                return redirect("admin_user_access")

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            user.first_name = full_name
            user.is_staff = is_staff
            user.is_active = is_active
            user.save()

            Person.objects.create(
                user=user,
                name=full_name or username,
                email=email
            )

            UserSetting.objects.get_or_create(user=user)

            messages.success(request, "User created successfully.")
            return redirect("admin_user_access")

        if action == "update_user":
            user_id = request.POST.get("user_id")
            target_user = get_object_or_404(User, id=user_id)

            username = request.POST.get("username", "").strip()
            email = request.POST.get("email", "").strip()
            full_name = request.POST.get("full_name", "").strip()
            new_password = request.POST.get("new_password", "").strip()

            new_is_staff = bool(request.POST.get("is_staff"))
            new_is_active = bool(request.POST.get("is_active"))

            if target_user == request.user and not new_is_staff:
                messages.error(request, "You cannot remove your own admin access.")
                return redirect("admin_user_access")

            if target_user == request.user and not new_is_active:
                messages.error(request, "You cannot deactivate your own account.")
                return redirect("admin_user_access")

            if username and User.objects.exclude(id=target_user.id).filter(username=username).exists():
                messages.error(request, "This username is already used by another account.")
                return redirect("admin_user_access")

            target_user.username = username or target_user.username
            target_user.email = email
            target_user.first_name = full_name
            target_user.is_staff = new_is_staff
            target_user.is_active = new_is_active

            if new_password:
                target_user.set_password(new_password)

            target_user.save()

            person = getattr(target_user, "person", None)

            if person:
                person.name = full_name or target_user.username
                person.email = email
                person.save()
            else:
                Person.objects.create(
                    user=target_user,
                    name=full_name or target_user.username,
                    email=email
                )

            UserSetting.objects.get_or_create(user=target_user)

            messages.success(request, "User access updated successfully.")
            return redirect("admin_user_access")

        if action == "delete_user":
            user_id = request.POST.get("user_id")
            target_user = get_object_or_404(User, id=user_id)

            if target_user == request.user:
                messages.error(request, "You cannot delete your own account.")
                return redirect("admin_user_access")

            username = target_user.username
            target_user.delete()

            messages.success(request, f"{username} was deleted successfully.")
            return redirect("admin_user_access")

    context = {
        "users": users,
        "search": search,
        "selected_role": role,
        "selected_status": status,
        "total_users": User.objects.count(),
        "total_admins": User.objects.filter(is_staff=True).count(),
        "total_active": User.objects.filter(is_active=True).count(),
        "total_inactive": User.objects.filter(is_active=False).count(),
    }

    return render(request, "admin_user_access.html", context)


@login_required
def teams_view(request):

    person = getattr(request.user, "person", None)
    user_department = None
    if person and person.team:
        user_department = person.team.department

    teams = Team.objects.select_related("department", "team_leader")

    if not request.user.is_staff:
        if user_department:
            teams = teams.filter(department=user_department)
        else:
            teams = teams.none()

    teams = teams.order_by("name")

    search = request.GET.get("search", "").strip()
    department = request.GET.get("department", "").strip()
    sort = request.GET.get("sort", "name").strip()

    if search:
        teams = teams.filter(name__icontains=search)

    if department and request.user.is_staff:
        teams = teams.filter(department_id=department)
    if sort == "members":
        teams = sorted(teams, key=lambda t: t.total_members(), reverse=True)
    elif sort == "repositories":
        teams = sorted(teams, key=lambda t: t.total_repositories(), reverse=True)
    elif sort == "newest":
        teams = teams.order_by("-created_at")
    else:
        teams = teams.order_by("name")

    departments = Department.objects.all().order_by("name")

    return render(request, "teams.html", {
        "teams": teams,
        "departments": departments,
        "search": search,
        "selected_department": department,
        "sort": sort,
    })


@login_required
def team_detail(request, id):
    team = get_object_or_404(
        Team.objects.select_related("department", "team_leader"),
        id=id
    )

    active_tab = request.GET.get("tab", "overview")

    if active_tab not in ["overview", "members", "repositories", "dependencies"]:
        active_tab = "overview"

    members = Person.objects.filter(team=team).order_by("name")

    leader_in_members = False

    if team.team_leader:
        leader_in_members = members.filter(id=team.team_leader.id).exists()

    repositories = Repository.objects.filter(team=team).order_by("name")

    dependencies = TeamDependency.objects.filter(
        source_team=team
    ).select_related("target_team").order_by("target_team__name")

    incoming_dependencies = TeamDependency.objects.filter(
        target_team=team
    ).select_related("source_team").order_by("source_team__name")

    team_messages = Message.objects.filter(
        receiver=team
    ).select_related("sender").order_by("-created_at")[:5]

    team_events = ScheduleEvent.objects.filter(
        team=team
    ).order_by("date", "start_time")[:5]

    team_activities = Activity.objects.filter(
        related_team=team
    ).order_by("-created_at")[:5]

    return render(request, "team_detail.html", {
        "team": team,
        "active_tab": active_tab,
        "members": members,
        "leader_in_members": leader_in_members,
        "repositories": repositories,
        "dependencies": dependencies,
        "incoming_dependencies": incoming_dependencies,
        "team_messages": team_messages,
        "team_events": team_events,
        "team_activities": team_activities,
    })


@login_required
def departments_view(request):

    person = getattr(request.user, "person", None)
    user_department = None
    if person and person.team:
        user_department = person.team.department

    if request.user.is_staff:
        departments = Department.objects.all().order_by("name")
    else:
        if user_department:
            departments = Department.objects.filter(id=user_department.id)
        else:
            departments = Department.objects.none()

    return render(request, "departments.html", {
        "departments": departments
    })

@login_required
def messages_view(request):
    person = getattr(request.user, "person", None)
    active_tab = request.GET.get("tab", "inbox")

    if active_tab not in ["inbox", "sent"]:
        active_tab = "inbox"

    if person is None:
        inbox = Message.objects.none()
        sent = Message.objects.none()
        unread_count = 0
    else:
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
        "inbox_count": inbox.count(),
        "sent_count": sent.count(),
        "active_tab": active_tab,
    })


@login_required
def new_message(request):
    teams = Team.objects.all().order_by("name")
    person = getattr(request.user, "person", None)

    if request.method == "POST":
        team_id = request.POST.get("team")
        subject = request.POST.get("subject")
        body = request.POST.get("body")

        if person is None:
            messages.error(request, "Your user profile is not connected to a Person record.")
            return redirect("new_message")

        if not team_id or not subject or not body:
            messages.error(request, "All fields required.")
            return redirect("new_message")

        team = get_object_or_404(Team, id=team_id)

        Message.objects.create(
            sender=person,
            receiver=team,
            subject=subject,
            body=body,
            is_read=False
        )

        Activity.objects.create(
            title="New message sent",
            description=f"{person.name} sent a message to {team.name}.",
            related_team=team
        )

        messages.success(request, "Message sent successfully.")
        return redirect("messages")

    return render(request, "new_message.html", {
        "teams": teams
    })


@login_required
def message_detail(request, id):
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
    original = get_object_or_404(
        Message.objects.select_related("sender", "receiver"),
        id=id
    )

    person = getattr(request.user, "person", None)

    if request.method == "POST":
        body = request.POST.get("body")

        if person is None:
            messages.error(request, "Your user profile is not connected to a Person record.")
            return redirect("messages")

        if not body:
            messages.error(request, "Reply message cannot be empty.")
            return redirect("reply_message", id=id)

        Message.objects.create(
            sender=person,
            receiver=original.receiver,
            subject="Re: " + original.subject,
            body=body,
            is_read=False
        )

        Activity.objects.create(
            title="Message replied",
            description=f"{person.name} replied to {original.subject}.",
            related_team=original.receiver
        )

        messages.success(request, "Reply sent successfully.")
        return redirect("messages")

    return render(request, "reply_message.html", {
        "original": original
    })


@login_required
def schedule_view(request):
    teams = Team.objects.all().order_by("name")
    events = ScheduleEvent.objects.select_related("team").order_by("date", "start_time")

    selected_team = request.GET.get("team", "").strip()
    search = request.GET.get("search", "").strip()

    if selected_team:
        events = events.filter(team_id=selected_team)

    if search:
        events = events.filter(title__icontains=search)

    if request.method == "POST":
        title = request.POST.get("title")
        team_id = request.POST.get("team")
        date = request.POST.get("date")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        platform = request.POST.get("platform")
        notes = request.POST.get("notes")

        if not title or not date or not start_time or not end_time:
            messages.error(request, "Title, date, start time and end time are required.")
            return redirect("schedule")

        team = Team.objects.filter(id=team_id).first() if team_id else None

        event = ScheduleEvent.objects.create(
            title=title,
            team=team,
            date=date,
            start_time=start_time,
            end_time=end_time,
            platform=platform,
            notes=notes
        )

        Activity.objects.create(
            title="New meeting scheduled",
            description=f"{event.title} was scheduled.",
            related_team=team
        )

        messages.success(request, "Meeting scheduled successfully.")
        return redirect("schedule")

    total_events = ScheduleEvent.objects.count()
    total_teams_with_events = Team.objects.filter(scheduleevent__isnull=False).distinct().count()
    next_event = ScheduleEvent.objects.select_related("team").order_by("date", "start_time").first()

    return render(request, "schedule.html", {
        "events": events,
        "teams": teams,
        "selected_team": selected_team,
        "search": search,
        "total_events": total_events,
        "total_teams_with_events": total_teams_with_events,
        "next_event": next_event,
    })


@login_required
def settings_view(request):
    setting, created = UserSetting.objects.get_or_create(user=request.user)
    departments = Department.objects.all().order_by("name")
    person = getattr(request.user, "person", None)

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        job_title = request.POST.get("job_title", "").strip()
        department_id = request.POST.get("department", "").strip()
        phone = request.POST.get("phone", "").strip()

        profile_visibility = request.POST.get("profile_visibility", "public")
        default_view = request.POST.get("default_view", "dashboard")
        theme = request.POST.get("theme", "light")
        language = request.POST.get("language", "English")
        timezone = request.POST.get("timezone", "UTC")

        setting.email_notifications = bool(request.POST.get("email_notifications"))
        setting.message_notifications = bool(request.POST.get("message_notifications"))
        setting.meeting_notifications = bool(request.POST.get("meeting_notifications"))

        setting.job_title = job_title
        setting.profile_visibility = profile_visibility
        setting.default_view = default_view
        setting.theme = theme
        setting.language = language
        setting.timezone = timezone

        if department_id:
            setting.department = Department.objects.filter(id=department_id).first()
        else:
            setting.department = None

        setting.save()

        request.user.email = email
        request.user.first_name = full_name
        request.user.save()

        if person:
            person.name = full_name or person.name
            person.email = email
            person.phone = phone
            person.role = job_title

            if request.FILES.get("photo"):
                person.photo = request.FILES.get("photo")

            person.save()
        else:
            Person.objects.create(
                user=request.user,
                name=full_name or request.user.username,
                email=email,
                phone=phone,
                role=job_title,
                photo=request.FILES.get("photo") if request.FILES.get("photo") else None,
            )

        messages.success(request, "Settings saved successfully.")
        return redirect("settings")

    return render(request, "settings.html", {
        "setting": setting,
        "departments": departments,
        "person": person,
    })


@login_required
def profile_view(request):
    person = getattr(request.user, "person", None)
    user_setting, created = UserSetting.objects.get_or_create(user=request.user)

    user_team = None
    user_department = None
    team_members = Person.objects.none()
    user_messages_sent = Message.objects.none()
    user_schedule_events = ScheduleEvent.objects.none()

    if person:
        user_team = person.team

        if user_team:
            user_department = user_team.department
            team_members = Person.objects.filter(team=user_team).order_by("name")
            user_schedule_events = ScheduleEvent.objects.filter(team=user_team).order_by("date", "start_time")[:5]

        user_messages_sent = Message.objects.filter(sender=person).select_related("receiver").order_by("-created_at")[:5]

    context = {
        "person": person,
        "user_setting": user_setting,
        "user_team": user_team,
        "user_department": user_department,
        "team_members": team_members,
        "user_messages_sent": user_messages_sent,
        "user_schedule_events": user_schedule_events,
        "email": request.user.email,
        "username": request.user.username,
    }

    return render(request, "profile.html", context)


@login_required
def organisation_map_view(request):
    departments = Department.objects.all().order_by("name")
    person = getattr(request.user, "person", None)
    user_department = None
    if person and person.team:
        user_department = person.team.department

    if request.user.is_staff:
        teams = Team.objects.select_related("department", "team_leader").order_by("name")
        people = Person.objects.select_related("team").order_by("name")
    else:
        if user_department:
            teams = Team.objects.filter(department=user_department)
            people = Person.objects.filter(team__department=user_department)
        else:
            teams = Team.objects.none()
            people = Person.objects.none()
            
    dependencies = TeamDependency.objects.select_related(
        "source_team",
        "target_team"
    ).order_by("source_team__name", "target_team__name")

    context = {
        "departments": departments,
        "teams": teams,
        "people": people,
        "dependencies": dependencies,
        "total_departments": departments.count(),
        "total_teams": teams.count(),
        "total_people": people.count(),
        "total_dependencies": dependencies.count(),
    }

    return render(request, "organisation_map.html", context)


def test_email(request):
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