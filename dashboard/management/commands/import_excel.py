import pandas as pd
from django.core.management.base import BaseCommand
from dashboard.models import Department, Team, Person


class Command(BaseCommand):
    help = "Import teams data from Excel"

    def handle(self, *args, **kwargs):

        file_path = "data/teams.xlsx"

        df = pd.read_excel(file_path)

        for _, row in df.iterrows():

            dept_name = str(row["Department"]).strip()
            team_leader_name = str(row["Team Leader"]).strip()
            dept_head_name = str(row["Department Head"]).strip()
            team_name = str(row["Team Name"]).strip()

            # Create/get Department Head
            dept_head, _ = Person.objects.get_or_create(name=dept_head_name)

            # Create/get Department
            department, _ = Department.objects.get_or_create(
                name=dept_name,
                defaults={"department_head": dept_head}
            )

            # If department already exists but has no head → set it
            if not department.department_head:
                department.department_head = dept_head
                department.save()

            # Create/get Team Leader
            team_leader, _ = Person.objects.get_or_create(name=team_leader_name)

            # Create Team
            Team.objects.get_or_create(
                name=team_name,
                department=department,
                defaults={"team_leader": team_leader}
            )

        self.stdout.write(self.style.SUCCESS("Excel data imported successfully"))