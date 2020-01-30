# Generated by Django 2.2.9 on 2020-01-29 13:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('beacon', '0016_auto_20200126_2026'),
    ]

    operations = [
        migrations.AddField(
            model_name='chapterrevision',
            name='guide',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chapter_revisions', to='beacon.Guide'),
        ),
        migrations.AddField(
            model_name='explainrevision',
            name='chapter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='explain_revisions', to='beacon.Chapter'),
        ),
        migrations.AddField(
            model_name='explainrevision',
            name='guide',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='explain_revisions', to='beacon.Guide'),
        ),
    ]
