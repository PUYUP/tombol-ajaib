# Generated by Django 2.2.9 on 2020-01-03 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beacon', '0002_auto_20191229_1226'),
    ]

    operations = [
        migrations.AddField(
            model_name='chapter',
            name='stage',
            field=models.BigIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='introduction',
            name='stage',
            field=models.BigIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='section',
            name='stage',
            field=models.BigIntegerField(null=True),
        ),
    ]
