from django.contrib import admin

from custom_admin import ModelAdmin
from custom_admin.admin import admin_site
from test_project.recipes.models import Recipe


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    readonly_fields = ('id',)

    fieldsets = (
        (None, {
            'fields': (('id', 'name'), 'description'),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Advanced options', {
            # 'description': 'A big description with lots of text',
            'classes': ('collapse',),
            'fields': ('number', 'ingredients'),
        }),
    )


class RecipeCustomAdmin(ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    readonly_fields = ('id',)

    fieldsets = (
        (None, {
            'fields': (('id', 'name'), 'description'),
        }),
        ('Advanced options', {
            'description': 'A big description with lots of text',
            'classes': ('collapse',),
            # 'fields': ('number', 'ingredients'),
            'fields': ('number', 'picture'),
        }),
        ('Dates', {
            'description': 'Dates description',
            'classes': ('collapse',),
            # 'fields': ('number', 'ingredients'),
            'fields': ('created', 'updated_date', 'updated_time'),
        }),
    )


admin.site.register(Recipe, RecipeAdmin)
admin_site.register(Recipe, RecipeCustomAdmin)
