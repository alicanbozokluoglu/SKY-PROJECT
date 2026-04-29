from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Person(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=100)

    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    team_leader = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name="leaders"
    )

    department_head = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name="heads"
    )

    jira_project = models.CharField(max_length=200, blank=True, null=True)

    development_focus = models.TextField(blank=True, null=True)
    tech_stack = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name