# Generated by Django 2.2.9 on 2020-01-09 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beacon', '0006_auto_20200104_0957'),
    ]

    operations = [
        migrations.AddField(
            model_name='chapterrevision',
            name='step',
            field=models.IntegerField(default=1, null=True),
        ),
        migrations.AddField(
            model_name='sectionrevision',
            name='step',
            field=models.IntegerField(default=1, null=True),
        ),
    ]
