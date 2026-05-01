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
        blank=True
    )

    def __str__(self):
        return self.name


class Message(models.Model):
    sender = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="received_messages")

    subject = models.CharField(max_length=200)
    body = models.TextField()

    is_read = models.BooleanField(default=False)  # ✅ IMPORTANT
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject