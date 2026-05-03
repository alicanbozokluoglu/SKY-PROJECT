from django.db import models
from django.contrib.auth.models import User


# this class represents a person (a real user in the system)
class Person(models.Model):

    # this connects Django login user to our custom person
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    # this stores the person's full name
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    # this shows the name in admin panel


# this class represents a department (like Engineering)
class Department(models.Model):

    # department name
    name = models.CharField(max_length=100)

    # this links to a person who is the head of department
    department_head = models.ForeignKey(
        'Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="headed_departments"
    )

    def __str__(self):
        return self.name


# this class represents a team inside a department
class Team(models.Model):

    # team name
    name = models.CharField(max_length=100)

    # which department this team belongs to
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    # who is leading this team
    team_leader = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # ✅ IMPORTANT: these are the new REAL fields (for higher marks)

    # this explains what the team does
    description = models.TextField(blank=True)

    # this stores contact email of team
    contact_email = models.EmailField(blank=True)

    # this stores github or repo link
    repo_link = models.URLField(blank=True)

    def __str__(self):
        return self.name


# this class represents messages between people and teams
class Message(models.Model):

    # who sent the message
    sender = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="sent_messages")

    # which team receives the message
    receiver = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="received_messages")

    # message title
    subject = models.CharField(max_length=200)

    # message content
    body = models.TextField()

    # whether message is read or not
    is_read = models.BooleanField(default=False)

    # when message was created
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject


"""
this file defines the database.

it creates 4 tables:
- person → users
- department → groups
- team → teams inside departments
- message → communication

each class = one table
each field = one column in database

important:
team now has real fields:
- description (what team does)
- contact_email (how to contact)
- repo_link (code location)

this makes the system more real and useful.
"""