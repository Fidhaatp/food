from django.db import models


class User(models.Model):
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
