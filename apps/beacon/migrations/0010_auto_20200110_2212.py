# Generated by Django 2.2.9 on 2020-01-10 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beacon', '0009_auto_20200110_1953'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='introduction',
            name='label',
        ),
        migrations.AlterField(
            model_name='introduction',
            name='description',
            field=models.TextField(max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='introduction',
            name='order',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
