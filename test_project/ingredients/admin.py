# -*- coding: utf-8 -*-
# Python imports

# Django imports
from django.contrib import admin

# Custom admin imports
from custom_admin.admin import admin_site

# App imports
from test_project.ingredients.models import Ingredient


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')


admin.site.register(Ingredient, IngredientAdmin)
admin_site.register(Ingredient, IngredientAdmin)