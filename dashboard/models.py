from django.db import models
from django.contrib.auth.models import User


# ✅ PERSON FIRST (VERY IMPORTANT)
class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# ✅ DEPARTMENT
class Department(models.Model):
    name = models.CharField(max_length=100)

    department_head = models.ForeignKey(
        'Person',  # string is fine here
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="headed_departments"
    )

    def __str__(self):
        return self.name


# ✅ TEAM
class Team(models.Model):
    name = models.CharField(max_length=100)

    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    team_leader = models.ForeignKey(
        Person,   # now works because Person is defined above
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


# ✅ MESSAGE
class Message(models.Model):
    sender = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="received_messages")

    subject = models.CharField(max_length=200)
    body = models.TextField()

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject
    
"""This file defines the database.
It creates tables for departments, people, teams, and messages.
Each model represents a table, and each field is a column."""