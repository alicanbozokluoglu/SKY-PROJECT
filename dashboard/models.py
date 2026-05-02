from django.db import models
# this imports Django tools to create database tables


class Department(models.Model):
    name = models.CharField(max_length=100)

    department_head = models.ForeignKey(
        'Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="headed_departments"
    )

    def __str__(self):
        return self.name

class Person(models.Model):
    # this creates a table for people (users, team leaders, etc.)

    name = models.CharField(max_length=100)
    # stores person's name

    def __str__(self):
        return self.name
    # shows name instead of object id


class Team(models.Model):
    # this creates a table for teams

    name = models.CharField(max_length=100)
    # team name

    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    # this connects each team to a department
    # CASCADE means: if department is deleted → team is also deleted

    team_leader = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    # this connects a team to a person (leader)
    # SET_NULL means: if leader is deleted → this becomes empty (null)
    # null=True means database allows empty
    # blank=True means form allows empty

    def __str__(self):
        return self.name
    # shows team name


class Message(models.Model):
    # this creates a table for messages

    sender = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="sent_messages")
    # who sent the message
    # CASCADE = if sender is deleted → message is deleted

    receiver = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="received_messages")
    # which team receives the message

    subject = models.CharField(max_length=200)
    # message title

    body = models.TextField()
    # message content (long text)

    is_read = models.BooleanField(default=False)
    # this tracks if message is read or not
    # default = False (unread)

    created_at = models.DateTimeField(auto_now_add=True)
    # automatically saves time when message is created

    def __str__(self):
        return self.subject
    # shows subject when printing message

"""This file defines the database.
It creates tables for departments, people, teams, and messages.
Each model represents a table, and each field is a column."""