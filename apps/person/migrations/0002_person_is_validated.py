# Generated by Django 2.2.9 on 2020-02-02 11:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='is_validated',
            field=models.BooleanField(default=False, null=True),
        ),
    ]