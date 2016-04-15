from django.db import models
from django.db.models import FileField


class ModelWithFileField(models.Model):
    file = FileField(upload_to="default_storage", null=True)
