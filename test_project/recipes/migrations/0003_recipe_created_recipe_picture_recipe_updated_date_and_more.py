# Generated by Django 4.0.6 on 2022-08-02 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_rename_time_recipe_number_alter_recipe_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='created',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='recipe',
            name='picture',
            field=models.FileField(null=True, upload_to=''),
        ),
        migrations.AddField(
            model_name='recipe',
            name='updated_date',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='recipe',
            name='updated_time',
            field=models.TimeField(null=True),
        ),
    ]
