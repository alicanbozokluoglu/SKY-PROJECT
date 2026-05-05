# This imports Django test tools.
from django.test import TestCase, Client

# This imports Django user accounts.
from django.contrib.auth.models import User

# This helps find page URLs by their name.
from django.urls import reverse

# This runs Django terminal commands inside tests.
from django.core.management import call_command

# This lets the test fake something instead of really running it.
from unittest.mock import patch

# This imports pandas to make fake Excel data.
import pandas as pd

# This imports Django validation error.
from django.core.exceptions import ValidationError

# This imports database tables used in tests.
from .models import (
    Department, Team, Person, UserSetting,
    Repository, TeamDependency, Message,
    Activity, ScheduleEvent
)


# This class creates common fake data for many tests.
class BaseTestSetup(TestCase):

    # This function runs before each test and prepares users, department, person, team and members.
    def setUp(self):
        self.client = Client()

        # This creates a normal user and an admin user.
        self.user = User.objects.create_user(username="user", password="pass123")
        self.admin = User.objects.create_user(username="admin", password="pass123", is_staff=True)

        # This creates one department.
        self.department = Department.objects.create(name="IT")

        # This creates one person connected to the normal user.
        self.person = Person.objects.create(user=self.user, name="Test User")

        # This creates one team with the person as leader.
        self.team = Team.objects.create(
            name="Dev Team",
            department=self.department,
            team_leader=self.person
        )

        # This puts the person inside the team.
        self.person.team = self.team
        self.person.save()

        # This creates five extra team members.
        for i in range(5):
            Person.objects.create(name=f"Member {i}", team=self.team)


# This class tests login and register pages.
class AuthTests(BaseTestSetup):

    # This test checks if correct login works.
    def test_login_success(self):
        response = self.client.post(reverse("login"), {
            "username": "user",
            "password": "pass123"
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)

    # This test checks if wrong password fails.
    def test_login_fail(self):
        response = self.client.post(reverse("login"), {
            "username": "user",
            "password": "wrong"
        })
        self.assertEqual(response.status_code, 200)

    # This test checks if a new user can register.
    def test_register_user(self):
        self.client.post(reverse("register"), {
            "fullname": "New User",
            "username": "newuser",
            "email": "test@test.com",
            "password": "12345678",
            "confirm_password": "12345678"
        })
        self.assertTrue(User.objects.filter(username="newuser").exists())