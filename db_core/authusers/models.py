from django.db import models

class OktaUser(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    okta_id = models.CharField(max_length=255, unique=True)
    last_login = models.DateTimeField(auto_now=True)
