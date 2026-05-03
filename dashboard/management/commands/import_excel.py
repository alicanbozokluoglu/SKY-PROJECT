import pandas as pd
# this lets us read Excel files

from django.core.management.base import BaseCommand
# this lets us create a custom Django command (run from terminal)

from django.contrib.auth.models import User
# this is Django's built-in user system (login, password, etc.)

from dashboard.models import Department, Team, Person
# these are your database tables from "models.py"


class Command(BaseCommand):
    # this creates a custom command you can run in terminal

    help = "Import teams + users from Excel"
    # this description shows when you run help in terminal


    def create_user(self, name):
        # this function creates a login user from a name

        username = name.lower().replace(" ", ".")
        # example: "John Smith" → "john.smith"

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": f"{username}@sky.com"}
        )
        # this checks:
        # → if user exists → use it
        # → if not → create new user

        if created:
            # only run if new user was created
            user.set_password("Password123!")
            # set a default password

            user.save()
            # save user to database

        return user
        # return the user so we can use it later


    def handle(self, *args, **kwargs):
        # this is the main function that runs when command is executed

        file_path = "data/teams.xlsx"
        # this is the Excel file location

        df = pd.read_excel(file_path)
        # this loads the Excel file into a table (DataFrame)


        # this loop goes through every row in Excel
        for _, row in df.iterrows():

            dept_name = row["Department"]
            team_leader_name = row["Team Leader"]
            dept_head_name = row["Department Head"]
            team_name = row["Team Name"]
            # get values from each column


            # this skips empty rows (very important)
            if pd.isna(team_leader_name) or pd.isna(team_name):
                continue


            # clean data (remove spaces)
            dept_name = str(dept_name).strip()
            team_leader_name = str(team_leader_name).strip()
            dept_head_name = str(dept_head_name).strip()
            team_name = str(team_name).strip()


            # -------------------------
            # CREATE USERS (LOGIN ACCOUNTS)
            # -------------------------
            leader_user = self.create_user(team_leader_name)
            head_user = self.create_user(dept_head_name)


            # -------------------------
            # CREATE PERSON OBJECTS (PROFILE DATA)
            # -------------------------
            team_leader, _ = Person.objects.get_or_create(
                name=team_leader_name
            )
            # create person if not exists

            if not team_leader.user:
                # if person is not linked to a user yet
                team_leader.user = leader_user
                team_leader.save()
                # connect person to login account


            dept_head, _ = Person.objects.get_or_create(
                name=dept_head_name
            )

            if not dept_head.user:
                dept_head.user = head_user
                dept_head.save()


            # -------------------------
            # CREATE DEPARTMENT
            # -------------------------
            department, _ = Department.objects.get_or_create(
                name=dept_name
            )

            if not department.department_head:
                # if department has no head yet
                department.department_head = dept_head
                department.save()


            # -------------------------
            # CREATE TEAM
            # -------------------------
            Team.objects.get_or_create(
                name=team_name,
                department=department,
                defaults={"team_leader": team_leader}
            )
            # create team and link it to department and leader


        # this prints a success message in terminal
        self.stdout.write(self.style.SUCCESS("✅ Excel data + users imported"))

"""This file takes data from Excel and puts it into database.

It creates:

users (login accounts)
people
departments
teams"""