from django.test import TestCase
# this imports Django testing tool
# it helps us check if our code works correctly

from django.contrib.auth.models import User
# this is the built-in user system (login, password, etc.)

from django.urls import reverse
# this helps us find URLs from "urls.py" using names

from .models import Department, Team, Person
# this imports our database tables from "models.py"


# this section tests the database models
# it checks if data like teams and users are created correctly
class ModelTest(TestCase):

    def setUp(self):
        # this function runs before each test
        # it creates sample data for testing

        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        # this creates a test login user

        self.person = Person.objects.create(
            name="Test Person",
            user=self.user
        )
        # this creates a person and links it to the user

        self.department = Department.objects.create(
            name="Engineering",
            department_head=self.person
        )
        # this creates a department and assigns a head

        self.team = Team.objects.create(
            name="Backend Team",
            department=self.department,
            team_leader=self.person
        )
        # this creates a team and connects it to department and leader


    def test_team_created(self):
        # this test checks if the team name is saved correctly
        self.assertEqual(self.team.name, "Backend Team")


    def test_department_link(self):
        # this test checks if the team is linked to the correct department
        self.assertEqual(self.team.department.name, "Engineering")


    def test_person_link(self):
        # this test checks if the person is linked to the correct user
        self.assertEqual(self.person.user.username, "testuser")


# this section tests the pages (views)
# it checks if pages load and behave correctly
class ViewTest(TestCase):

    def setUp(self):
        # create a test user for login tests
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )


    def test_login_page_loads(self):
        # this test checks if the login page opens correctly
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        # 200 means the page loaded successfully


    def test_dashboard_requires_login(self):
        # this test checks if dashboard blocks users who are not logged in
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 302)
        # 302 means it redirects (because login is required)


    def test_dashboard_after_login(self):
        # this test logs in and checks if dashboard works
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        # 200 means the page works after login


# this section tests login system (authentication)
# it checks if login works correctly
class AuthTest(TestCase):

    def setUp(self):
        # create a user for login testing
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )


    def test_login_success(self):
        # this test checks if login works with correct password
        login = self.client.login(
            username="testuser",
            password="testpass123"
        )
        self.assertTrue(login)
        # True means login was successful


    def test_login_fail(self):
        # this test checks if login fails with wrong password
        login = self.client.login(
            username="testuser",
            password="wrongpass"
        )
        self.assertFalse(login)
        # False means login failed (correct behaviour)

# this section tests search function
# it checks if search finds correct teams

class SearchTest(TestCase):

    def setUp(self):
        # create user and data
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )

        self.person = Person.objects.create(name="Olivia Carter", user=self.user)

        self.department = Department.objects.create(name="Engineering")

        self.team1 = Team.objects.create(
            name="Backend Team",
            department=self.department,
            team_leader=self.person
        )

        self.team2 = Team.objects.create(
            name="Frontend Team",
            department=self.department,
            team_leader=self.person
        )

    def test_search_by_name(self):   # ✅ NOW INSIDE CLASS

        # login first
        self.client.login(username="testuser", password="testpass123")

        # search for backend
        response = self.client.get(reverse("teams"), {"q": "Backend"})
        # check page loads
        self.assertEqual(response.status_code, 200)
        
        self.assertTemplateUsed(response, "teams.html")

        # check correct results
        self.assertContains(response, "Backend Team")
        self.assertNotContains(response, "Frontend Team")
        
# this section tests new team fields
# it checks if description, email and repo are saved
class TeamFieldTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )

        self.person = Person.objects.create(name="Test Person", user=self.user)

        self.department = Department.objects.create(name="Engineering")

        self.team = Team.objects.create(
            name="DevOps Team",
            department=self.department,
            team_leader=self.person,
            description="Handles deployment",
            contact_email="devops@sky.com",
            repo_link="https://github.com/devops"
        )

    def test_description_saved(self):
        self.assertEqual(self.team.description, "Handles deployment")

    def test_email_saved(self):
        self.assertEqual(self.team.contact_email, "devops@sky.com")

    def test_repo_saved(self):
        self.assertEqual(self.team.repo_link, "https://github.com/devops")


"""This file checks if your system works.

It checks:

data is saved correctly
pages open correctly
login works"""
