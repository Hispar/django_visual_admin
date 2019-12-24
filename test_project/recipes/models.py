# -*- coding: utf-8 -*-
# Python imports

# Django imports
from django.db import models


# App imports


class Recipe(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    time = models.IntegerField()
    ingredients = models.ManyToManyField('ingredients.Ingredient')
