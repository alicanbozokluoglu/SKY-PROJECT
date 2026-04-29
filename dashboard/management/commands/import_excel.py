import pandas as pd
from django.core.management.base import BaseCommand
from dashboard.models import Department, Person, Team


class Command(BaseCommand):
    help = "Import team data from Excel"

    def handle(self, *args, **kwargs):

        file_path = "data/teams.xlsx"  # adjust if needed

        df = pd.read_excel(file_path)

        for _, row in df.iterrows():

            department_name = str(row["Department"]).strip()
            leader_name = str(row["Team Leader"]).strip()
            head_name = str(row["Department Head"]).strip()
            team_name = str(row["Team Name"]).strip()

            jira_project = str(row.get("Jira Project Name", "")).strip()
            development_focus = str(row.get("Development Focus Areas", "")).strip()
            tech_stack = str(row.get("Key Skills & Technologies", "")).strip()

            if not team_name or team_name == "nan":
                continue

            department, _ = Department.objects.get_or_create(name=department_name)
            leader, _ = Person.objects.get_or_create(name=leader_name)
            head, _ = Person.objects.get_or_create(name=head_name)

            Team.objects.get_or_create(
                name=team_name,
                department=department,
                team_leader=leader,
                department_head=head,
                jira_project=jira_project,
                development_focus=development_focus,
                tech_stack=tech_stack
            )

        self.stdout.write(self.style.SUCCESS("✅ Data imported"))