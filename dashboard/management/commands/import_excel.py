import pandas as pd
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models import Department, Team, Person


class Command(BaseCommand):
    help = "Import teams + users from Excel"

    def create_user(self, name):
        username = name.lower().replace(" ", ".")

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": f"{username}@sky.com"}
        )

        if created:
            user.set_password("Password123!")
            user.save()

        return user

    def handle(self, *args, **kwargs):

        file_path = "data/teams.xlsx"
        df = pd.read_excel(file_path)

        for _, row in df.iterrows():

            dept_name = row["Department"]
            team_leader_name = row["Team Leader"]
            dept_head_name = row["Department Head"]
            team_name = row["Team Name"]

            # -------------------------
            # 🚫 SKIP EMPTY ROWS (CRITICAL FIX)
            # -------------------------
            if pd.isna(team_leader_name) or pd.isna(team_name):
                continue

            # Clean values
            dept_name = str(dept_name).strip()
            team_leader_name = str(team_leader_name).strip()
            dept_head_name = str(dept_head_name).strip()
            team_name = str(team_name).strip()

            # -------------------------
            # CREATE USERS
            # -------------------------
            leader_user = self.create_user(team_leader_name)
            head_user = self.create_user(dept_head_name)

            # -------------------------
            # CREATE PERSONS
            # -------------------------
            team_leader, _ = Person.objects.get_or_create(
                name=team_leader_name
            )
            if not team_leader.user:
                team_leader.user = leader_user
                team_leader.save()

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

        self.stdout.write(self.style.SUCCESS("✅ Excel data + users imported"))