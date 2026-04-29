from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    manager_name = models.CharField(max_length=100)
    manager_role = models.CharField(max_length=100)
    manager_image = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class Notification(models.Model):
    message = models.CharField(max_length=255)
    time = models.CharField(max_length=50)

    def __str__(self):
        return self.message


class Meeting(models.Model):
    title = models.CharField(max_length=200)
    time = models.CharField(max_length=100)

    def __str__(self):
        return self.title
