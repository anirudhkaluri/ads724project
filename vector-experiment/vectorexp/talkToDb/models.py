from django.db import models
from pgvector.django import VectorField
# Create your models here.

class Items(models.Model):
    #original_text = models.TextField()
    #embedding = models.TextField()  # This field type is a guess.
    embedding = VectorField(dimensions=384)

    class Meta:
        managed = False
        db_table = 'items'
