from django.db import models


class Recipe(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    number = models.IntegerField()
    ingredients = models.ManyToManyField('ingredients.Ingredient')
    updated_date = models.DateField(null=True)
    updated_time = models.TimeField(null=True)
    created = models.DateTimeField(null=True)
    picture = models.FileField(null=True)
