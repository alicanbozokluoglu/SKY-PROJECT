from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.management import call_command
from unittest.mock import patch
import pandas as pd
from django.core.exceptions import ValidationError
from .models import (
    Department, Team, Person, UserSetting,
    Repository, TeamDependency, Message,
    Activity, ScheduleEvent
)


class BaseTestSetup(TestCase):
    def setUp(self):
        self.client = Client()

        # Create users
        self.user = User.objects.create_user(username="user", password="pass123")
        self.admin = User.objects.create_user(username="admin", password="pass123", is_staff=True)

        # Create department
        self.department = Department.objects.create(name="IT")

        # Create person (leader)
        self.person = Person.objects.create(user=self.user, name="Test User")

        # Create team
        self.team = Team.objects.create(
            name="Dev Team",
            department=self.department,
            team_leader=self.person
        )

        self.person.team = self.team
        self.person.save()

        for i in range(5):
            Person.objects.create(name=f"Member {i}", team=self.team)

class AuthTests(BaseTestSetup):

    def test_login_success(self):
        response = self.client.post(reverse("login"), {
            "username": "user",
            "password": "pass123"
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)

    def test_login_fail(self):
        response = self.client.post(reverse("login"), {
            "username": "user",
            "password": "wrong"
        })
        self.assertEqual(response.status_code, 200)

    def test_register_user(self):
        self.client.post(reverse("register"), {
            "fullname": "New User",
            "username": "newuser",
            "email": "test@test.com",
            "password": "12345678",
            "confirm_password": "12345678"
        })
        self.assertTrue(User.objects.filter(username="newuser").exists())
# =========================
# MODEL TESTS
# =========================

class ModelTests(BaseTestSetup):

    def test_team_total_members_leader_not_in_team(self):
        leader = Person.objects.create(name="Leader")
        self.team.team_leader = leader
        self.team.save()

        self.assertEqual(self.team.total_members(), 6)

    def test_repository_creation(self):
        repo = Repository.objects.create(team=self.team, name="Repo1")
        self.assertEqual(repo.team, self.team)

    def test_dependency_creation(self):
        team2 = Team.objects.create(name="Team2")
        dep = TeamDependency.objects.create(source_team=self.team, target_team=team2)
        self.assertEqual(dep.source_team, self.team)

    def test_message_creation(self):
        msg = Message.objects.create(
            sender=self.person,
            receiver=self.team,
            subject="Hello",
            body="Test"
        )
        self.assertFalse(msg.is_read)

    def test_schedule_event(self):
        event = ScheduleEvent.objects.create(
            title="Meeting",
            team=self.team,
            date="2026-01-01",
            start_time="10:00",
            end_time="11:00"
        )
        self.assertEqual(event.team, self.team)

        team = Team(name="Small Team", department=self.department)

        with self.assertRaises(ValidationError):
            team.save()
    def test_team_minimum_members_validation(self):
        team = Team(name="Small Team", department=self.department)

        with self.assertRaises(ValidationError):
            team.save()
# =========================
# DASHBOARD TESTS
# =========================

class DashboardTests(BaseTestSetup):

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_logged_in(self):
        self.client.login(username="user", password="pass123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)


# =========================
# ADMIN TESTS
# =========================

class AdminTests(BaseTestSetup):

    def test_admin_access_denied(self):
        self.client.login(username="user", password="pass123")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_admin_access_allowed(self):
        self.client.login(username="admin", password="pass123")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_create_team(self):
        self.client.login(username="admin", password="pass123")

        response = self.client.post(reverse("admin_team_management"), {
            "action": "create_team",
            "name": "New Team"
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Team.objects.filter(name="New Team").exists())
        self.assertEqual(Activity.objects.count(), 1)

    def test_delete_team(self):
        self.client.login(username="admin", password="pass123")

        self.client.post(reverse("admin_team_management"), {
            "action": "delete_team",
            "team_id": self.team.id
        })

        self.assertFalse(Team.objects.filter(id=self.team.id).exists())


# =========================
# TEAMS
# =========================

class TeamTests(BaseTestSetup):

    def test_teams_page(self):
        self.client.login(username="user", password="pass123")
        response = self.client.get(reverse("teams"))
        self.assertEqual(response.status_code, 200)

    def test_team_detail(self):
        self.client.login(username="user", password="pass123")
        response = self.client.get(reverse("team_detail", args=[self.team.id]))
        self.assertEqual(response.status_code, 200)


# =========================
# MESSAGES
# =========================

class MessageTests(BaseTestSetup):

    def test_send_message(self):
        self.client.login(username="user", password="pass123")

        self.client.post(reverse("new_message"), {
            "team": self.team.id,
            "subject": "Test",
            "body": "Hello"
        })

        self.assertEqual(Message.objects.count(), 1)

    def test_reply_message(self):
        msg = Message.objects.create(
            sender=self.person,
            receiver=self.team,
            subject="Hi",
            body="Test"
        )

        self.client.login(username="user", password="pass123")

        self.client.post(reverse("reply_message", args=[msg.id]), {
            "body": "Reply"
        })

        self.assertEqual(Message.objects.count(), 2)

    def test_unread_message_count(self):
        self.team.team_leader = self.person
        self.team.save()

        Message.objects.create(
            sender=self.person,
            receiver=self.team,
            subject="Test",
            body="Test",
            is_read=False
        )

        self.client.login(username="user", password="pass123")
        response = self.client.get(reverse("messages"))

        self.assertContains(response, "1")


# =========================
# SCHEDULE
# =========================

class ScheduleTests(BaseTestSetup):

    def test_create_event(self):
        self.client.login(username="user", password="pass123")

        self.client.post(reverse("schedule"), {
            "title": "Meeting",
            "date": "2026-01-01",
            "start_time": "10:00",
            "end_time": "11:00"
        })

        self.assertEqual(ScheduleEvent.objects.count(), 1)


# =========================
# SETTINGS
# =========================

class SettingsTests(BaseTestSetup):

    def test_update_settings(self):
        self.client.login(username="user", password="pass123")

        self.client.post(reverse("settings"), {
            "full_name": "Updated Name",
            "email": "new@test.com"
        })

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated Name")


# =========================
# PROFILE
# =========================

class ProfileTests(BaseTestSetup):

    def test_profile_page(self):
        self.client.login(username="user", password="pass123")
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)


# =========================
# FILTERING
# =========================

class FilteringTests(BaseTestSetup):

    def setUp(self):
        super().setUp()
        self.client.login(username="user", password="pass123")
        Team.objects.create(name="Alpha Team", department=self.department)

    def test_search_filter(self):
        response = self.client.get(reverse("teams"), {"search": "Alpha"})
        self.assertContains(response, "Alpha Team")


# =========================
# EDGE CASES
# =========================

class EdgeCaseTests(BaseTestSetup):

    def test_register_missing_fields(self):
        response = self.client.post(reverse("register"), {
            "username": "",
            "password": ""
        })
        self.assertEqual(response.status_code, 302)

    def test_create_team_no_name(self):
        self.client.login(username="admin", password="pass123")

        response = self.client.post(reverse("admin_team_management"), {
            "action": "create_team",
            "name": ""
        })

        self.assertEqual(response.status_code, 302)


# =========================
# PERMISSIONS
# =========================

class PermissionEdgeTests(BaseTestSetup):

    def test_admin_cannot_delete_self(self):
        self.client.login(username="admin", password="pass123")

        response = self.client.post(reverse("admin_user_access"), {
            "action": "delete_user",
            "user_id": self.admin.id
        })

        self.assertEqual(response.status_code, 302)


# =========================
# IMPORT EXCEL
# =========================

class ImportExcelTests(TestCase):

    @patch("dashboard.management.commands.import_excel.pd.read_excel")
    def test_import_excel_skips_invalid_rows(self, mock_read_excel):
        data = {
            "Department": ["IT", "IT"],
            "Team Leader": ["John Doe", None],  # invalid row
            "Department Head": ["Jane Smith", "Jane Smith"],
            "Team Name": ["Dev Team", None]     # invalid row
        }

        mock_read_excel.return_value = pd.DataFrame(data)

        call_command("import_excel")

        # Only valid row should be created
        self.assertEqual(Team.objects.count(), 1)
        self.assertTrue(Team.objects.filter(name="Dev Team").exists())