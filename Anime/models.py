from django.db import models

# Create your models here.

class Anime(models.Model):
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=100)
    release_date = models.DateField()
    rating = models.FloatField()

class Character(models.Model):
    animeobj = models.ForeignKey(Anime,on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    descripcion = models.TextField()
