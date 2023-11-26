from django.db import models

class Invoice(models.Model):
    file = models.FileField(upload_to='invoices/')
