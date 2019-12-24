# -*- coding: utf-8 -*-
# Python imports

# 3rd Party imports
from django.contrib import admin

# Custom admin imports
from custom_admin.admin import admin_site

# App imports
from test_project.recipes.models import Recipe


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')



admin.site.register(Recipe, RecipeAdmin)
admin_site.register(Recipe, RecipeAdmin)
