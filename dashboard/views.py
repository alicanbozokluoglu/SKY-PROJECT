# Django shortcuts for rendering pages, redirects, and reading records safely.
from django.shortcuts import render, redirect, get_object_or_404

# Django authentication tools.
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

# Django messages and email tools.
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.db.models import Q

# Python tools.
import re

# Project models.
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
    UserActivity,
)


# Saves a user action into the personal activity history.
def log_user_activity(user_account, action_type, title, description="", related_team=None):
    if user_account and user_account.is_authenticated:
        UserActivity.objects.create(
            user=user_account,
            action_type=action_type,
            title=title,
            description=description,
            related_team=related_team,
        )


# Logs a user in and sends them to the correct page.
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("admin_dashboard")
        return redirect("dashboard")

    if request.method == "POST":
        entered_username = request.POST.get("username", "").strip()
        entered_password = request.POST.get("password", "")
        selected_role = request.POST.get("role", "")
        remember_choice = request.POST.get("remember")

        logged_user = authenticate(
            request,
            username=entered_username,
            password=entered_password,
        )

        if logged_user is not None:
            if selected_role == "admin" and not logged_user.is_staff:
                messages.error(request, "You are not authorized as admin.")
                return redirect("login")

            if selected_role == "user" and logged_user.is_staff:
                messages.error(request, "Admins must login from admin section.")
                return redirect("login")

            login(request, logged_user)

            if remember_choice == "on":
                request.session.set_expiry(60 * 60 * 24 * 30)
            else:
                request.session.set_expiry(0)

            request.session.modified = True

            if logged_user.is_staff:
                return redirect("admin_dashboard")

            return redirect("dashboard")

        messages.error(request, "Invalid login details")

    return render(request, "login.html")


# Logs the user out and clears the session.
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect("login")


# Creates a new user account.
def register_view(request):
    if request.method == "POST":
        full_name = request.POST.get("fullname")
        username = request.POST.get("username")
        email_address = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not full_name or not username or not email_address or not password or not confirm_password:
            messages.error(request, "All fields are required.")
            return redirect("register")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken.")
            return redirect("register")

        if User.objects.filter(email=email_address).exists():
            messages.error(request, "This email is already registered.")
            return redirect("register")

        new_user = User.objects.create_user(
            username=username,
            email=email_address,
            password=password,
        )
        new_user.first_name = full_name
        new_user.save()

        Person.objects.create(
            user=new_user,
            name=full_name,
            email=email_address,
        )

        UserSetting.objects.get_or_create(
            user=new_user,
            defaults={
                "language": "English UK",
                "background": "default",
            },
        )

        messages.success(request, "Account created successfully. You can now log in.")
        return redirect("login")

    return render(request, "register.html")


# Shows the normal user dashboard.
@login_required
def dashboard(request):
    current_person = getattr(request.user, "person", None)

    user_team_list = Team.objects.none()
    sent_message_list = Message.objects.none()
    upcoming_event_list = ScheduleEvent.objects.none()

    if current_person:
        user_team_list = Team.objects.filter(
            Q(members=current_person)
            | Q(extra_members=current_person)
            | Q(team_leader=current_person)
        ).select_related(
            "department",
            "team_leader",
        ).distinct()

        sent_message_list = Message.objects.filter(
            sender=current_person,
        ).select_related(
            "receiver",
        ).order_by("-created_at")[:5]

    upcoming_event_list = ScheduleEvent.objects.filter(
        created_by=request.user,
    ).select_related(
        "team",
    ).order_by("date", "start_time")[:5]

    personal_activity_list = UserActivity.objects.filter(
        user=request.user,
    ).select_related(
        "related_team",
    ).order_by("-created_at")[:10]

    recent_visit_activity_list = UserActivity.objects.filter(
        user=request.user,
        action_type="team_visit",
        related_team__isnull=False,
    ).select_related(
        "related_team",
        "related_team__department",
        "related_team__team_leader",
    ).order_by("-created_at")

    visited_team_ids = []
    recent_team_list = []

    for activity_item in recent_visit_activity_list:
        if activity_item.related_team_id not in visited_team_ids:
            activity_item.related_team.last_visited_at = activity_item.created_at
            visited_team_ids.append(activity_item.related_team_id)
            recent_team_list.append(activity_item.related_team)

        if len(recent_team_list) == 3:
            break

    if not recent_team_list:
        recent_team_list = list(user_team_list[:3])

    context = {
        "teams": recent_team_list,
        "personal_activities": personal_activity_list,
        "upcoming_events": upcoming_event_list,
        "sent_messages": sent_message_list,
        "total_user_teams": user_team_list.count(),
        "total_user_messages": Message.objects.filter(sender=current_person).count() if current_person else 0,
        "total_user_meetings": ScheduleEvent.objects.filter(created_by=request.user).count(),
        "total_user_actions": UserActivity.objects.filter(user=request.user).count(),
    }

    return render(request, "dashboard.html", context)


# Shows the admin dashboard and lets admins manage repositories, dependencies, and events.
@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access the admin dashboard.")
        return redirect("dashboard")

    team_list = Team.objects.filter(status="Active").select_related("department", "team_leader").order_by("name")
    department_list = Department.objects.all().order_by("name")
    person_list = Person.objects.select_related("team").order_by("name")
    repository_list = Repository.objects.select_related("team").order_by("name")
    dependency_list = TeamDependency.objects.select_related("source_team", "target_team").order_by("source_team__name", "target_team__name")
    event_list = ScheduleEvent.objects.select_related("team").order_by("date", "start_time")
    user_list = User.objects.all().order_by("-date_joined")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_repository":
            repository_name = request.POST.get("repository_name", "").strip()
            team_id = request.POST.get("team")
            technology = request.POST.get("technology", "").strip()
            last_updated = request.POST.get("last_updated") or None
            repository_url = request.POST.get("url", "").strip()
            description = request.POST.get("description", "").strip()

            if not repository_name or not team_id:
                messages.error(request, "Repository name and team are required.")
                return redirect("admin_dashboard")

            selected_team = get_object_or_404(Team, id=team_id)

            new_repository = Repository.objects.create(
                name=repository_name,
                team=selected_team,
                technology=technology,
                last_updated=last_updated,
                url=repository_url,
                description=description,
            )

            Activity.objects.create(
                title="Repository created",
                description=f"{new_repository.name} was created for {selected_team.name}.",
                related_team=selected_team,
            )

            messages.success(request, "Repository created successfully.")
            return redirect("admin_dashboard")

        if action == "update_repository":
            repository_id = request.POST.get("repository_id")
            selected_repository = get_object_or_404(Repository, id=repository_id)

            repository_name = request.POST.get("repository_name", "").strip()
            team_id = request.POST.get("team")
            technology = request.POST.get("technology", "").strip()
            last_updated = request.POST.get("last_updated") or None
            repository_url = request.POST.get("url", "").strip()
            description = request.POST.get("description", "").strip()

            if not repository_name or not team_id:
                messages.error(request, "Repository name and team are required.")
                return redirect("admin_dashboard")

            selected_team = get_object_or_404(Team, id=team_id)

            selected_repository.name = repository_name
            selected_repository.team = selected_team
            selected_repository.technology = technology
            selected_repository.last_updated = last_updated
            selected_repository.url = repository_url
            selected_repository.description = description
            selected_repository.save()

            Activity.objects.create(
                title="Repository updated",
                description=f"{selected_repository.name} repository was updated.",
                related_team=selected_team,
            )

            messages.success(request, "Repository updated successfully.")
            return redirect("admin_dashboard")

        if action == "delete_repository":
            repository_id = request.POST.get("repository_id")
            selected_repository = get_object_or_404(Repository, id=repository_id)
            repository_name = selected_repository.name
            selected_team = selected_repository.team

            selected_repository.delete()

            Activity.objects.create(
                title="Repository deleted",
                description=f"{repository_name} repository was deleted.",
                related_team=selected_team,
            )

            messages.success(request, "Repository deleted successfully.")
            return redirect("admin_dashboard")

        if action == "create_dependency":
            source_team_id = request.POST.get("source_team")
            target_team_id = request.POST.get("target_team")
            dependency_type = request.POST.get("dependency_type", "").strip()
            dependency_status = "Active" if request.POST.get("is_active") else "Inactive"
            description = request.POST.get("description", "").strip()

            if not source_team_id or not target_team_id:
                messages.error(request, "Source team and target team are required.")
                return redirect("admin_dashboard")

            if source_team_id == target_team_id:
                messages.error(request, "A team cannot depend on itself.")
                return redirect("admin_dashboard")

            source_team = get_object_or_404(Team, id=source_team_id)
            target_team = get_object_or_404(Team, id=target_team_id)

            TeamDependency.objects.create(
                source_team=source_team,
                target_team=target_team,
                dependency_type=dependency_type,
                status=dependency_status,
                description=description,
            )

            Activity.objects.create(
                title="Dependency created",
                description=f"{source_team.name} now depends on {target_team.name}.",
                related_team=source_team,
            )

            messages.success(request, "Dependency created successfully.")
            return redirect("admin_dashboard")

        if action == "update_dependency":
            dependency_id = request.POST.get("dependency_id")
            selected_dependency = get_object_or_404(TeamDependency, id=dependency_id)

            source_team_id = request.POST.get("source_team")
            target_team_id = request.POST.get("target_team")
            dependency_type = request.POST.get("dependency_type", "").strip()
            dependency_status = "Active" if request.POST.get("is_active") else "Inactive"
            description = request.POST.get("description", "").strip()

            if not source_team_id or not target_team_id:
                messages.error(request, "Source team and target team are required.")
                return redirect("admin_dashboard")

            if source_team_id == target_team_id:
                messages.error(request, "A team cannot depend on itself.")
                return redirect("admin_dashboard")

            source_team = get_object_or_404(Team, id=source_team_id)
            target_team = get_object_or_404(Team, id=target_team_id)

            selected_dependency.source_team = source_team
            selected_dependency.target_team = target_team
            selected_dependency.dependency_type = dependency_type
            selected_dependency.status = dependency_status
            selected_dependency.description = description
            selected_dependency.save()

            Activity.objects.create(
                title="Dependency updated",
                description=f"{source_team.name} → {target_team.name} dependency was updated.",
                related_team=source_team,
            )

            messages.success(request, "Dependency updated successfully.")
            return redirect("admin_dashboard")

        if action == "delete_dependency":
            dependency_id = request.POST.get("dependency_id")
            selected_dependency = get_object_or_404(TeamDependency, id=dependency_id)
            source_team = selected_dependency.source_team
            target_team = selected_dependency.target_team

            selected_dependency.delete()

            Activity.objects.create(
                title="Dependency deleted",
                description=f"{source_team.name} → {target_team.name} dependency was deleted.",
                related_team=source_team,
            )

            messages.success(request, "Dependency deleted successfully.")
            return redirect("admin_dashboard")

        if action == "create_event":
            event_title = request.POST.get("event_title", "").strip()
            team_id = request.POST.get("team")
            event_date = request.POST.get("date")
            start_time = request.POST.get("start_time")
            end_time = request.POST.get("end_time")
            platform = request.POST.get("platform", "").strip()
            notes = request.POST.get("notes", "").strip()

            if not event_title or not event_date or not start_time or not end_time:
                messages.error(request, "Event title, date, start time and end time are required.")
                return redirect("admin_dashboard")

            selected_team = Team.objects.filter(id=team_id).first() if team_id else None

            new_event = ScheduleEvent.objects.create(
                title=event_title,
                team=selected_team,
                date=event_date,
                start_time=start_time,
                end_time=end_time,
                platform=platform,
                notes=notes,
                created_by=request.user,
            )

            Activity.objects.create(
                title="Event created",
                description=f"{new_event.title} was added to the schedule.",
                related_team=selected_team,
            )

            messages.success(request, "Event created successfully.")
            return redirect("admin_dashboard")

        if action == "update_event":
            event_id = request.POST.get("event_id")
            selected_event = get_object_or_404(ScheduleEvent, id=event_id)

            event_title = request.POST.get("event_title", "").strip()
            team_id = request.POST.get("team")
            event_date = request.POST.get("date")
            start_time = request.POST.get("start_time")
            end_time = request.POST.get("end_time")
            platform = request.POST.get("platform", "").strip()
            notes = request.POST.get("notes", "").strip()

            if not event_title or not event_date or not start_time or not end_time:
                messages.error(request, "Event title, date, start time and end time are required.")
                return redirect("admin_dashboard")

            selected_team = Team.objects.filter(id=team_id).first() if team_id else None

            selected_event.title = event_title
            selected_event.team = selected_team
            selected_event.date = event_date
            selected_event.start_time = start_time
            selected_event.end_time = end_time
            selected_event.platform = platform
            selected_event.notes = notes
            selected_event.save()

            Activity.objects.create(
                title="Event updated",
                description=f"{selected_event.title} event was updated.",
                related_team=selected_team,
            )

            messages.success(request, "Event updated successfully.")
            return redirect("admin_dashboard")

        if action == "delete_event":
            event_id = request.POST.get("event_id")
            selected_event = get_object_or_404(ScheduleEvent, id=event_id)
            event_title = selected_event.title
            selected_team = selected_event.team

            selected_event.delete()

            Activity.objects.create(
                title="Event deleted",
                description=f"{event_title} event was deleted.",
                related_team=selected_team,
            )

            messages.success(request, "Event deleted successfully.")
            return redirect("admin_dashboard")

    context = {
        "teams": team_list,
        "departments": department_list,
        "people": person_list,
        "repositories": repository_list,
        "dependencies": dependency_list,
        "events": event_list,
        "users": user_list,
        "total_users": User.objects.count(),
        "total_admins": User.objects.filter(is_staff=True).count(),
        "total_active_users": User.objects.filter(is_active=True).count(),
        "total_inactive_users": User.objects.filter(is_active=False).count(),
        "total_teams": Team.objects.count(),
        "total_departments": Department.objects.count(),
        "total_members": Person.objects.count(),
        "total_messages": Message.objects.count(),
        "total_meetings": ScheduleEvent.objects.count(),
        "total_repositories": Repository.objects.count(),
        "total_dependencies": TeamDependency.objects.count(),
        "assigned_teams": Team.objects.filter(department__isnull=False).count(),
        "unassigned_teams": Team.objects.filter(department__isnull=True).count(),
        "unread_messages": Message.objects.filter(is_read=False).count(),
        "latest_users": User.objects.order_by("-date_joined")[:6],
        "latest_teams": Team.objects.select_related("department", "team_leader").order_by("-created_at")[:6],
        "latest_messages": Message.objects.select_related("sender", "receiver").order_by("-created_at")[:6],
        "latest_events": ScheduleEvent.objects.select_related("team").order_by("date", "start_time")[:6],
        "activities": Activity.objects.select_related("related_team").order_by("-created_at")[:10],
    }

    return render(request, "admin_dashboard.html", context)


# Lets admins create, edit, filter, and delete teams.
@login_required
def admin_team_management(request):
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access team management.")
        return redirect("dashboard")

    department_list = Department.objects.all().order_by("name")
    person_list = Person.objects.all().order_by("name")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_team":
            team_name = request.POST.get("name", "").strip()
            department_id = request.POST.get("department")
            leader_id = request.POST.get("team_leader")
            status = request.POST.get("status", "Active").strip()
            location = request.POST.get("location", "").strip()
            description = request.POST.get("description", "").strip()
            active_project_count = request.POST.get("active_projects_count") or 0
            github_link = request.POST.get("github_link", "").strip()
            documentation_link = request.POST.get("documentation_link", "").strip()
            calendar_link = request.POST.get("calendar_link", "").strip()

            if not team_name:
                messages.error(request, "Team name is required.")
                return redirect("admin_team_management")

            selected_department = Department.objects.filter(id=department_id).first() if department_id else None
            selected_leader = Person.objects.filter(id=leader_id).first() if leader_id else None

            new_team = Team.objects.create(
                name=team_name,
                department=selected_department,
                team_leader=selected_leader,
                status=status or "Active",
                location=location,
                description=description,
                active_projects_count=active_project_count,
                github_link=github_link,
                documentation_link=documentation_link,
                calendar_link=calendar_link,
            )

            Activity.objects.create(
                title="Team created",
                description=f"{new_team.name} was created from Team Management.",
                related_team=new_team,
            )

            messages.success(request, "Team created successfully.")
            return redirect("admin_team_management")

        if action == "update_team":
            team_id = request.POST.get("team_id")
            selected_team = get_object_or_404(Team, id=team_id)
            team_name = request.POST.get("name", "").strip()

            if not team_name:
                messages.error(request, "Team name is required.")
                return redirect("admin_team_management")

            selected_team.name = team_name
            selected_team.department = Department.objects.filter(id=request.POST.get("department")).first() if request.POST.get("department") else None
            selected_team.team_leader = Person.objects.filter(id=request.POST.get("team_leader")).first() if request.POST.get("team_leader") else None
            selected_team.status = request.POST.get("status", "Active").strip() or "Active"
            selected_team.location = request.POST.get("location", "").strip()
            selected_team.description = request.POST.get("description", "").strip()
            selected_team.active_projects_count = request.POST.get("active_projects_count") or 0
            selected_team.github_link = request.POST.get("github_link", "").strip()
            selected_team.documentation_link = request.POST.get("documentation_link", "").strip()
            selected_team.calendar_link = request.POST.get("calendar_link", "").strip()
            selected_team.save()

            Activity.objects.create(
                title="Team updated",
                description=f"{selected_team.name} was updated from Team Management.",
                related_team=selected_team,
            )

            messages.success(request, "Team updated successfully.")
            return redirect("admin_team_management")

        if action == "delete_team":
            team_id = request.POST.get("team_id")
            selected_team = get_object_or_404(Team, id=team_id)
            team_name = selected_team.name
            selected_team.delete()

            Activity.objects.create(
                title="Team deleted",
                description=f"{team_name} was deleted from Team Management.",
                related_team=None,
            )

            messages.success(request, "Team deleted successfully.")
            return redirect("admin_team_management")

    team_list = Team.objects.select_related("department", "team_leader").order_by("name")

    search_text = request.GET.get("search", "").strip()
    selected_department = request.GET.get("department", "").strip()
    selected_status = request.GET.get("status", "").strip()

    if search_text:
        team_list = team_list.filter(name__icontains=search_text)

    if selected_department:
        team_list = team_list.filter(department_id=selected_department)

    if selected_status:
        team_list = team_list.filter(status__iexact=selected_status)

    context = {
        "teams": team_list,
        "departments": department_list,
        "people": person_list,
        "search": search_text,
        "selected_department": selected_department,
        "selected_status": selected_status,
        "total_teams": Team.objects.count(),
        "total_departments": Department.objects.count(),
        "total_members": Person.objects.count(),
        "total_repositories": Repository.objects.count(),
    }

    return render(request, "admin_team_management.html", context)


# Lets admins create, edit, and delete departments.
@login_required
def admin_department_management(request):
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access department management.")
        return redirect("dashboard")

    department_list = Department.objects.all().order_by("name")
    team_list = Team.objects.select_related("department", "team_leader").order_by("name")
    search_text = request.GET.get("search", "").strip()

    if search_text:
        department_list = department_list.filter(name__icontains=search_text)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_department":
            department_name = request.POST.get("name", "").strip()

            if not department_name:
                messages.error(request, "Department name is required.")
                return redirect("admin_department_management")

            if Department.objects.filter(name__iexact=department_name).exists():
                messages.error(request, "This department already exists.")
                return redirect("admin_department_management")

            new_department = Department.objects.create(name=department_name)

            Activity.objects.create(
                title="Department created",
                description=f"{new_department.name} department was created.",
                related_team=None,
            )

            messages.success(request, "Department created successfully.")
            return redirect("admin_department_management")

        if action == "update_department":
            department_id = request.POST.get("department_id")
            selected_department = get_object_or_404(Department, id=department_id)
            department_name = request.POST.get("name", "").strip()
            selected_team_ids = request.POST.getlist("team_ids")

            if not department_name:
                messages.error(request, "Department name is required.")
                return redirect("admin_department_management")

            if Department.objects.exclude(id=selected_department.id).filter(name__iexact=department_name).exists():
                messages.error(request, "Another department with this name already exists.")
                return redirect("admin_department_management")

            old_department_name = selected_department.name
            selected_department.name = department_name
            selected_department.save()

            Team.objects.filter(department=selected_department).exclude(id__in=selected_team_ids).update(department=None)
            Team.objects.filter(id__in=selected_team_ids).update(department=selected_department)

            Activity.objects.create(
                title="Department updated",
                description=f"{old_department_name} department was updated to {selected_department.name}.",
                related_team=None,
            )

            messages.success(request, "Department updated successfully.")
            return redirect("admin_department_management")

        if action == "delete_department":
            department_id = request.POST.get("department_id")
            selected_department = get_object_or_404(Department, id=department_id)
            department_name = selected_department.name

            Team.objects.filter(department=selected_department).update(department=None)
            selected_department.delete()

            Activity.objects.create(
                title="Department deleted",
                description=f"{department_name} department was deleted.",
                related_team=None,
            )

            messages.success(request, "Department deleted successfully.")
            return redirect("admin_department_management")

    context = {
        "departments": department_list,
        "teams": team_list,
        "total_departments": Department.objects.count(),
        "total_teams": Team.objects.count(),
        "assigned_teams": Team.objects.filter(department__isnull=False).count(),
        "unassigned_teams": Team.objects.filter(department__isnull=True).count(),
        "search": search_text,
    }

    return render(request, "admin_department_management.html", context)


# Lets admins create, edit, filter, and delete user accounts.
@login_required
def admin_user_access(request):
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access user access management.")
        return redirect("dashboard")

    user_list = User.objects.all().order_by("username")

    search_text = request.GET.get("search", "").strip()
    selected_role = request.GET.get("role", "").strip()
    selected_status = request.GET.get("status", "").strip()

    if search_text:
        user_list = user_list.filter(username__icontains=search_text)

    if selected_role == "admin":
        user_list = user_list.filter(is_staff=True)

    if selected_role == "user":
        user_list = user_list.filter(is_staff=False)

    if selected_status == "active":
        user_list = user_list.filter(is_active=True)

    if selected_status == "inactive":
        user_list = user_list.filter(is_active=False)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_user":
            username = request.POST.get("username", "").strip()
            email_address = request.POST.get("email", "").strip()
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

            new_user = User.objects.create_user(
                username=username,
                email=email_address,
                password=password,
            )
            new_user.first_name = full_name
            new_user.is_staff = is_staff
            new_user.is_active = is_active
            new_user.save()

            Person.objects.create(
                user=new_user,
                name=full_name or username,
                email=email_address,
            )

            UserSetting.objects.get_or_create(
                user=new_user,
                defaults={"language": "English UK", "background": "default"},
            )

            messages.success(request, "User created successfully.")
            return redirect("admin_user_access")

        if action == "update_user":
            user_id = request.POST.get("user_id")
            target_user = get_object_or_404(User, id=user_id)

            username = request.POST.get("username", "").strip()
            email_address = request.POST.get("email", "").strip()
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
            target_user.email = email_address
            target_user.first_name = full_name
            target_user.is_staff = new_is_staff
            target_user.is_active = new_is_active

            if new_password:
                target_user.set_password(new_password)

            target_user.save()

            target_person = getattr(target_user, "person", None)

            if target_person:
                target_person.name = full_name or target_user.username
                target_person.email = email_address
                target_person.save()
            else:
                Person.objects.create(
                    user=target_user,
                    name=full_name or target_user.username,
                    email=email_address,
                )

            UserSetting.objects.get_or_create(
                user=target_user,
                defaults={"language": "English UK", "background": "default"},
            )

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
        "users": user_list,
        "search": search_text,
        "selected_role": selected_role,
        "selected_status": selected_status,
        "total_users": User.objects.count(),
        "total_admins": User.objects.filter(is_staff=True).count(),
        "total_active": User.objects.filter(is_active=True).count(),
        "total_inactive": User.objects.filter(is_active=False).count(),
    }

    return render(request, "admin_user_access.html", context)


# Shows the team directory page.
@login_required
def teams_view(request):
    current_person = getattr(request.user, "person", None)

    user_department = None
    if current_person and current_person.team:
        user_department = current_person.team.department

    team_list = Team.objects.select_related("department", "team_leader")

    if not request.user.is_staff:
        if user_department:
            team_list = team_list.filter(department=user_department)
        else:
            team_list = team_list.none()

    team_list = team_list.order_by("name")

    search_text = request.GET.get("search", "").strip()
    selected_department = request.GET.get("department", "").strip()
    selected_sort = request.GET.get("sort", "name").strip()

    if search_text:
        team_list = team_list.filter(
            Q(name__icontains=search_text)
            | Q(team_leader__name__icontains=search_text)
            | Q(department__name__icontains=search_text)
        )

    if selected_department and request.user.is_staff:
        team_list = team_list.filter(department_id=selected_department)

    if selected_sort == "members":
        team_list = sorted(team_list, key=lambda team_item: team_item.total_members(), reverse=True)
    elif selected_sort == "repositories":
        team_list = sorted(team_list, key=lambda team_item: team_item.total_repositories(), reverse=True)
    elif selected_sort == "newest":
        team_list = team_list.order_by("-created_at")
    else:
        team_list = team_list.order_by("name")

    for team_item in team_list:
        member_list = Person.objects.filter(
            Q(team=team_item)
            | Q(teams=team_item)
            | Q(leading_teams=team_item)
        ).distinct().order_by("name")

        member_count = member_list.count()
        team_item.card_members = list(member_list[:5])
        team_item.extra_members_count = max(member_count - 5, 0)
        team_item.card_member_count = member_count

    department_list = Department.objects.all().order_by("name")

    return render(request, "teams.html", {
        "teams": team_list,
        "departments": department_list,
        "search": search_text,
        "selected_department": selected_department,
        "sort": selected_sort,
    })


# Shows one team detail page.
@login_required
def team_detail(request, id):
    selected_team = get_object_or_404(
        Team.objects.select_related("department", "team_leader"),
        id=id,
    )

    log_user_activity(
        request.user,
        "team_visit",
        f"Visited {selected_team.name}",
        f"You opened the {selected_team.name} team page.",
        related_team=selected_team,
    )

    active_tab = request.GET.get("tab", "overview")

    if active_tab not in ["overview", "members", "repositories", "dependencies"]:
        active_tab = "overview"

    member_list = Person.objects.filter(
        Q(team=selected_team)
        | Q(teams=selected_team)
        | Q(leading_teams=selected_team)
    ).distinct().order_by("name")

    leader_in_members = False
    if selected_team.team_leader:
        leader_in_members = member_list.filter(id=selected_team.team_leader.id).exists()

    repository_list = Repository.objects.filter(team=selected_team).order_by("name")

    outgoing_dependency_list = TeamDependency.objects.filter(
        source_team=selected_team,
        status="Active",
    ).select_related("target_team").order_by("target_team__name")

    incoming_dependency_list = TeamDependency.objects.filter(
        target_team=selected_team,
        status="Active",
    ).select_related("source_team").order_by("source_team__name")

    team_message_list = Message.objects.filter(
        receiver=selected_team,
    ).select_related("sender").order_by("-created_at")[:5]

    team_event_list = ScheduleEvent.objects.filter(
        team=selected_team,
    ).order_by("date", "start_time")[:5]

    team_activity_list = Activity.objects.filter(
        related_team=selected_team,
    ).order_by("-created_at")[:5]

    return render(request, "team_detail.html", {
        "team": selected_team,
        "active_tab": active_tab,
        "members": member_list,
        "leader_in_members": leader_in_members,
        "repositories": repository_list,
        "dependencies": outgoing_dependency_list,
        "incoming_dependencies": incoming_dependency_list,
        "team_messages": team_message_list,
        "team_events": team_event_list,
        "team_activities": team_activity_list,
    })


# Shows the departments page.
@login_required
def departments_view(request):
    current_person = getattr(request.user, "person", None)

    user_department = None
    if current_person and current_person.team:
        user_department = current_person.team.department

    if request.user.is_staff:
        department_list = Department.objects.all().order_by("name")
    else:
        if user_department:
            department_list = Department.objects.filter(id=user_department.id)
        else:
            department_list = Department.objects.none()

    return render(request, "departments.html", {
        "departments": department_list,
    })


# Shows inbox and sent messages.
@login_required
def messages_view(request):
    current_person = getattr(request.user, "person", None)
    active_tab = request.GET.get("tab", "inbox")

    if active_tab not in ["inbox", "sent"]:
        active_tab = "inbox"

    if current_person is None:
        inbox_list = Message.objects.none()
        sent_list = Message.objects.none()
        unread_count = 0
    else:
        user_team_list = current_person.teams.all()

        if current_person.team:
            user_team_list = user_team_list | Team.objects.filter(id=current_person.team.id)

        inbox_list = Message.objects.filter(
            receiver__in=user_team_list,
        ).select_related("sender", "receiver").order_by("-created_at")

        sent_list = Message.objects.filter(
            sender=current_person,
        ).select_related("receiver").order_by("-created_at")

        unread_count = inbox_list.filter(is_read=False).count()

    return render(request, "messages.html", {
        "inbox": inbox_list,
        "sent": sent_list,
        "unread_count": unread_count,
        "inbox_count": inbox_list.count(),
        "sent_count": sent_list.count(),
        "active_tab": active_tab,
    })


# Lets a user send a new message to a team.
@login_required
def new_message(request):
    team_list = Team.objects.all().order_by("name")
    current_person = getattr(request.user, "person", None)

    if request.method == "POST":
        team_id = request.POST.get("team")
        subject = request.POST.get("subject")
        body = request.POST.get("body")

        if current_person is None:
            messages.error(request, "Your user profile is not connected to a Person record.")
            return redirect("new_message")

        if not team_id or not subject or not body:
            messages.error(request, "All fields required.")
            return redirect("new_message")

        selected_team = get_object_or_404(Team, id=team_id)

        Message.objects.create(
            sender=current_person,
            receiver=selected_team,
            subject=subject,
            body=body,
            is_read=False,
        )

        Activity.objects.create(
            title="New message sent",
            description=f"{current_person.name} sent a message to {selected_team.name}.",
            related_team=selected_team,
        )

        log_user_activity(
            request.user,
            "message_sent",
            "Message sent",
            f"You sent a message to {selected_team.name}: {subject}",
            related_team=selected_team,
        )

        messages.success(request, "Message sent successfully.")
        return redirect("messages")

    return render(request, "new_message.html", {
        "teams": team_list,
    })


# Shows one message and marks it as read.
@login_required
def message_detail(request, id):
    selected_message = get_object_or_404(
        Message.objects.select_related("sender", "receiver"),
        id=id,
    )

    if not selected_message.is_read:
        selected_message.is_read = True
        selected_message.save()

    return render(request, "message_detail.html", {
        "message": selected_message,
    })


# Lets a user reply to a message.
@login_required
def reply_message(request, id):
    original_message = get_object_or_404(
        Message.objects.select_related("sender", "receiver"),
        id=id,
    )

    current_person = getattr(request.user, "person", None)

    if request.method == "POST":
        reply_body = request.POST.get("body")

        if current_person is None:
            messages.error(request, "Your user profile is not connected to a Person record.")
            return redirect("messages")

        if not reply_body:
            messages.error(request, "Reply message cannot be empty.")
            return redirect("reply_message", id=id)

        Message.objects.create(
            sender=current_person,
            receiver=original_message.receiver,
            subject="Re: " + original_message.subject,
            body=reply_body,
            is_read=False,
        )

        Activity.objects.create(
            title="Message replied",
            description=f"{current_person.name} replied to {original_message.subject}.",
            related_team=original_message.receiver,
        )

        log_user_activity(
            request.user,
            "message_reply",
            "Message replied",
            f"You replied to: {original_message.subject}",
            related_team=original_message.receiver,
        )

        messages.success(request, "Reply sent successfully.")
        return redirect("messages")

    return render(request, "reply_message.html", {
        "original": original_message,
    })


# Shows the schedule page and lets users create events.
@login_required
def schedule_view(request):
    team_list = Team.objects.all().order_by("name")
    event_list = ScheduleEvent.objects.select_related("team").order_by("date", "start_time")

    selected_team = request.GET.get("team", "").strip()
    search_text = request.GET.get("search", "").strip()

    if selected_team:
        event_list = event_list.filter(team_id=selected_team)

    if search_text:
        event_list = event_list.filter(title__icontains=search_text)

    if request.method == "POST":
        event_title = request.POST.get("title")
        team_id = request.POST.get("team")
        event_date = request.POST.get("date")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        platform = request.POST.get("platform")
        notes = request.POST.get("notes")

        if not event_title or not event_date or not start_time or not end_time:
            messages.error(request, "Title, date, start time and end time are required.")
            return redirect("schedule")

        selected_team_object = Team.objects.filter(id=team_id).first() if team_id else None

        new_event = ScheduleEvent.objects.create(
            title=event_title,
            team=selected_team_object,
            date=event_date,
            start_time=start_time,
            end_time=end_time,
            platform=platform,
            notes=notes,
            created_by=request.user,
        )

        Activity.objects.create(
            title="New meeting scheduled",
            description=f"{new_event.title} was scheduled.",
            related_team=selected_team_object,
        )

        log_user_activity(
            request.user,
            "schedule_created",
            "Meeting scheduled",
            f"You scheduled {new_event.title}.",
            related_team=selected_team_object,
        )

        messages.success(request, "Meeting scheduled successfully.")
        return redirect("schedule")

    total_events = ScheduleEvent.objects.count()
    total_teams_with_events = Team.objects.filter(scheduleevent__isnull=False).distinct().count()
    next_event = ScheduleEvent.objects.select_related("team").order_by("date", "start_time").first()

    return render(request, "schedule.html", {
        "events": event_list,
        "teams": team_list,
        "selected_team": selected_team,
        "search": search_text,
        "total_events": total_events,
        "total_teams_with_events": total_teams_with_events,
        "next_event": next_event,
    })


# Lets a user change email, phone, photo, password, and page settings.
@login_required
def settings_view(request):
    current_person = getattr(request.user, "person", None)

    user_setting, created = UserSetting.objects.get_or_create(
        user=request.user,
        defaults={
            "language": "English UK",
            "background": "default",
        },
    )

    if created:
        user_setting.language = "English UK"
        user_setting.background = "default"
        user_setting.save()

    if request.method == "POST":
        email_address = request.POST.get("email", "").strip()
        job_title = request.POST.get("job_title", "").strip()
        phone_number = request.POST.get("phone", "").strip()
        language = request.POST.get("language", "English UK").strip()
        background = request.POST.get("background", "default").strip()
        uploaded_photo = request.FILES.get("photo")

        old_password = request.POST.get("old_password", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if language not in ["English UK", "English US"]:
            messages.error(request, "Please choose English UK or English US.")
            return redirect("settings")

        if background not in ["default", "black"]:
            messages.error(request, "Please choose a valid background option.")
            return redirect("settings")

        if phone_number and not re.match(r"^\+44\d{10}$", phone_number):
            messages.error(request, "Phone number must start with +44 and contain 10 digits after it. Example: +447123456789")
            return redirect("settings")

        if old_password or new_password or confirm_password:
            if not old_password or not new_password or not confirm_password:
                messages.error(request, "Please fill old password, new password and confirm password.")
                return redirect("settings")

            if not request.user.check_password(old_password):
                messages.error(request, "Old password is incorrect.")
                return redirect("settings")

            if new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
                return redirect("settings")

            if len(new_password) < 6:
                messages.error(request, "New password must be at least 6 characters.")
                return redirect("settings")

            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)

        request.user.email = email_address
        request.user.save()

        if current_person:
            current_person.email = email_address
            current_person.role = job_title
            current_person.phone = phone_number

            if uploaded_photo:
                current_person.photo = uploaded_photo

            current_person.save()

        user_setting.job_title = job_title
        user_setting.language = language
        user_setting.background = background
        user_setting.save()

        log_user_activity(
            request.user,
            "settings_updated",
            "Settings updated",
            "You updated your profile or account settings.",
        )

        messages.success(request, "Settings updated successfully.")
        return redirect("settings")

    return render(request, "settings.html", {
        "person": current_person,
        "setting": user_setting,
    })


# Shows the logged-in user's profile page.
@login_required
def profile_view(request):
    current_person = getattr(request.user, "person", None)

    user_setting, created = UserSetting.objects.get_or_create(
        user=request.user,
        defaults={
            "language": "English UK",
            "background": "default",
        },
    )

    user_team = None
    user_department = None
    team_member_list = Person.objects.none()
    sent_message_list = Message.objects.none()
    schedule_event_list = ScheduleEvent.objects.none()

    if current_person:
        user_team = current_person.team

        if user_team:
            user_department = user_team.department
            team_member_list = Person.objects.filter(
                Q(team=user_team)
                | Q(teams=user_team)
                | Q(leading_teams=user_team)
            ).distinct().order_by("name")

            schedule_event_list = ScheduleEvent.objects.filter(
                team=user_team,
            ).order_by("date", "start_time")[:5]

        sent_message_list = Message.objects.filter(
            sender=current_person,
        ).select_related("receiver").order_by("-created_at")[:5]

    context = {
        "person": current_person,
        "user_setting": user_setting,
        "user_team": user_team,
        "user_department": user_department,
        "team_members": team_member_list,
        "user_messages_sent": sent_message_list,
        "user_schedule_events": schedule_event_list,
        "email": request.user.email,
        "username": request.user.username,
    }

    return render(request, "profile.html", context)


# Shows the organisation map page.
@login_required
def organisation_map_view(request):
    department_list = Department.objects.all().order_by("name")
    current_person = getattr(request.user, "person", None)

    user_department = None
    if current_person and current_person.team:
        user_department = current_person.team.department

    if request.user.is_staff:
        team_list = Team.objects.select_related("department", "team_leader").order_by("name")
        person_list = Person.objects.select_related("team").order_by("name")
    else:
        if user_department:
            team_list = Team.objects.filter(department=user_department)
            person_list = Person.objects.filter(team__department=user_department)
        else:
            team_list = Team.objects.none()
            person_list = Person.objects.none()

    dependency_list = TeamDependency.objects.filter(
        status="Active",
        source_team__status="Active",
        target_team__status="Active",
    ).select_related(
        "source_team",
        "target_team",
    ).order_by("source_team__name", "target_team__name")

    context = {
        "departments": department_list,
        "teams": team_list,
        "people": person_list,
        "dependencies": dependency_list,
        "total_departments": department_list.count(),
        "total_teams": team_list.count(),
        "total_people": person_list.count(),
        "total_dependencies": dependency_list.count(),
    }

    return render(request, "organisation_map.html", context)


# Searches teams, departments, and people from one search box.
@login_required
def global_search(request):
    search_query = request.GET.get("q", "").strip()

    team_results = Team.objects.none()
    department_results = Department.objects.none()
    person_results = Person.objects.none()

    if search_query:
        team_results = Team.objects.select_related(
            "department",
            "team_leader",
        ).filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(location__icontains=search_query)
            | Q(status__icontains=search_query)
            | Q(department__name__icontains=search_query)
            | Q(team_leader__name__icontains=search_query)
        ).distinct().order_by("name")

        department_results = Department.objects.filter(
            Q(name__icontains=search_query)
            | Q(team__name__icontains=search_query)
            | Q(team__team_leader__name__icontains=search_query)
        ).distinct().order_by("name")

        person_results = Person.objects.select_related(
            "user",
            "team",
            "team__department",
        ).prefetch_related(
            "teams",
            "teams__department",
        ).filter(
            Q(name__icontains=search_query)
            | Q(role__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(phone__icontains=search_query)
            | Q(team__name__icontains=search_query)
            | Q(team__department__name__icontains=search_query)
            | Q(teams__name__icontains=search_query)
            | Q(teams__department__name__icontains=search_query)
        ).distinct().order_by("name")

    total_results = team_results.count() + department_results.count() + person_results.count()

    return render(request, "global_search.html", {
        "query": search_query,
        "teams": team_results,
        "departments": department_results,
        "people": person_results,
        "total_results": total_results,
    })


# Shows another person's profile page.
@login_required
def person_profile(request, id):
    selected_person = get_object_or_404(
        Person.objects.select_related(
            "user",
            "team",
            "team__department",
        ).prefetch_related(
            "teams",
            "teams__department",
        ),
        id=id,
    )

    user_setting = None

    if selected_person.user:
        user_setting, created = UserSetting.objects.get_or_create(
            user=selected_person.user,
            defaults={
                "language": "English UK",
                "background": "default",
            },
        )

    user_team = None
    user_department = None
    team_member_list = Person.objects.none()
    sent_message_list = Message.objects.none()
    schedule_event_list = ScheduleEvent.objects.none()

    user_team = selected_person.team

    if user_team:
        user_department = user_team.department

        team_member_list = Person.objects.filter(
            Q(team=user_team)
            | Q(teams=user_team)
            | Q(leading_teams=user_team)
        ).distinct().order_by("name")

        schedule_event_list = ScheduleEvent.objects.filter(
            team=user_team,
        ).order_by("date", "start_time")[:5]

    sent_message_list = Message.objects.filter(
        sender=selected_person,
    ).select_related("receiver").order_by("-created_at")[:5]

    context = {
        "person": selected_person,
        "user_setting": user_setting,
        "user_team": user_team,
        "user_department": user_department,
        "team_members": team_member_list,
        "user_messages_sent": sent_message_list,
        "user_schedule_events": schedule_event_list,
        "email": selected_person.email,
        "username": selected_person.user.username if selected_person.user else selected_person.name,
    }

    return render(request, "profile.html", context)


# Sends a test email and shows if it worked.
@login_required
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

    except Exception as error:
        return HttpResponse(f"ERROR: {error}")


# Lets admins assign people to teams or remove them from teams.
@login_required
def admin_person_management(request):
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access person management.")
        return redirect("dashboard")

    department_list = Department.objects.all().order_by("name")
    team_list = Team.objects.select_related("department").order_by("department__name", "name")

    person_list = Person.objects.select_related(
        "team",
        "team__department",
        "user",
    ).prefetch_related(
        "teams",
        "teams__department",
    ).order_by("name")

    search_text = request.GET.get("search", "").strip()
    selected_department = request.GET.get("department", "").strip()
    selected_team = request.GET.get("team", "").strip()

    if search_text:
        person_list = person_list.filter(name__icontains=search_text)

    if selected_department:
        person_list = person_list.filter(
            Q(team__department_id=selected_department)
            | Q(teams__department_id=selected_department)
        ).distinct()

    if selected_team:
        if selected_team == "unassigned":
            person_list = person_list.filter(team__isnull=True, teams__isnull=True)
        else:
            person_list = person_list.filter(
                Q(team_id=selected_team)
                | Q(teams__id=selected_team)
            ).distinct()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_person_teams":
            person_id = request.POST.get("person_id")
            selected_team_ids = request.POST.getlist("team_ids")

            selected_person = get_object_or_404(Person, id=person_id)
            selected_team_list = Team.objects.filter(id__in=selected_team_ids)

            selected_person.teams.set(selected_team_list)

            first_team = selected_team_list.first()
            selected_person.team = first_team if first_team else None
            selected_person.save()

            team_names = ", ".join(selected_team_list.values_list("name", flat=True))

            Activity.objects.create(
                title="Person teams updated",
                description=f"{selected_person.name} assigned to: {team_names if team_names else 'No team'}.",
                related_team=first_team,
            )

            messages.success(request, f"{selected_person.name} team assignments updated.")
            return redirect("admin_person_management")

        if action == "remove_from_all_teams":
            person_id = request.POST.get("person_id")
            selected_person = get_object_or_404(Person, id=person_id)

            selected_person.teams.clear()
            selected_person.team = None
            selected_person.save()

            Activity.objects.create(
                title="Person removed from teams",
                description=f"{selected_person.name} was removed from all teams.",
                related_team=None,
            )

            messages.success(request, f"{selected_person.name} removed from all teams.")
            return redirect("admin_person_management")

    context = {
        "people": person_list,
        "departments": department_list,
        "teams": team_list,
        "search": search_text,
        "selected_department": selected_department,
        "selected_team": selected_team,
        "total_people": Person.objects.count(),
        "assigned_people": Person.objects.filter(
            Q(team__isnull=False) | Q(teams__isnull=False)
        ).distinct().count(),
        "unassigned_people": Person.objects.filter(
            team__isnull=True,
            teams__isnull=True,
        ).count(),
        "total_teams": Team.objects.count(),
    }

    return render(request, "admin_person_management.html", context)
