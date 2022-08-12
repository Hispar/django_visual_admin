from django.contrib import admin

from custom_admin import ModelAdmin
from custom_admin.admin import admin_site
from test_project.ingredients.models import Ingredient


class IngredientCustomAdmin(ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')


admin.site.register(Ingredient, IngredientAdmin)
admin_site.register(Ingredient, IngredientCustomAdmin)
