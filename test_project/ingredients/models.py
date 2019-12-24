# -*- coding: utf-8 -*-
# Python imports

# Django imports
from django.db import models


# App imports


class Ingredient(models.Model):
    name = models.CharField(max_length=255)

