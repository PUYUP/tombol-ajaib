# Generated by Django 2.2.9 on 2019-12-29 05:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('beacon', '0001_initial'),
        ('person', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vote',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='votes', to='person.Person'),
        ),
        migrations.AddField(
            model_name='tag',
            name='content_type',
            field=models.ForeignKey(limit_choices_to=models.Q(app_label='beacon'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='tag',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tags', to='person.Person'),
        ),
        migrations.AddField(
            model_name='rating',
            name='content_type',
            field=models.ForeignKey(limit_choices_to=models.Q(app_label='beacon'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='rating',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ratings', to='person.Person'),
        ),
        migrations.AddField(
            model_name='sectionrevision',
            name='changelog',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='section_revisions', to='beacon.ChangeLog'),
        ),
        migrations.AddField(
            model_name='sectionrevision',
            name='content',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='section_revisions', to='beacon.Content'),
        ),
        migrations.AddField(
            model_name='sectionrevision',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='section_revisions', to='person.Person'),
        ),
        migrations.AddField(
            model_name='sectionrevision',
            name='section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='section_revisions', to='beacon.Section'),
        ),
        migrations.AddField(
            model_name='section',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sections', to='person.Person'),
        ),
        migrations.AddField(
            model_name='section',
            name='chapter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='beacon.Chapter'),
        ),
        migrations.AddField(
            model_name='chapterrevision',
            name='changelog',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chapter_revisions', to='beacon.ChangeLog'),
        ),
        migrations.AddField(
            model_name='chapterrevision',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chapter_revisions', to='person.Person'),
        ),
        migrations.AddField(
            model_name='chapterrevision',
            name='chapter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chapter_revisions', to='beacon.Chapter'),
        ),
        migrations.AddField(
            model_name='chapter',
            name='guide',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chapters', to='beacon.Guide'),
        ),
        migrations.AddField(
            model_name='chapter',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chapters', to='person.Person'),
        ),
        migrations.AddField(
            model_name='introduction',
            name='content_type',
            field=models.ForeignKey(limit_choices_to=models.Q(app_label='beacon'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='introduction',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='introductions', to='person.Person'),
        ),
        migrations.AddField(
            model_name='guiderevision',
            name='changelog',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='guide_revisions', to='beacon.ChangeLog'),
        ),
        migrations.AddField(
            model_name='guiderevision',
            name='guide',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guide_revisions', to='beacon.Guide'),
        ),
        migrations.AddField(
            model_name='guiderevision',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='guide_revisions', to='person.Person'),
        ),
        migrations.AddField(
            model_name='guide',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='beacon', to='beacon.Category'),
        ),
        migrations.AddField(
            model_name='guide',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='beacon', to='person.Person'),
        ),
        migrations.AddField(
            model_name='content',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contents', to='person.Person'),
        ),
        migrations.AddField(
            model_name='changelog',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='changelogs', to='person.Person'),
        ),
        migrations.AddField(
            model_name='category',
            name='parent',
            field=models.ForeignKey(blank=True, limit_choices_to={'parent__isnull': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='childs', to='beacon.Category'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='content_type',
            field=models.ForeignKey(limit_choices_to=models.Q(app_label='beacon'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attachments', to='person.Person'),
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together={('object_id', 'creator')},
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together={('label',)},
        ),
        migrations.AlterUniqueTogether(
            name='rating',
            unique_together={('object_id', 'creator')},
        ),
        migrations.AlterUniqueTogether(
            name='sectionrevision',
            unique_together={('label',)},
        ),
        migrations.AlterUniqueTogether(
            name='chapterrevision',
            unique_together={('label',)},
        ),
        migrations.AlterUniqueTogether(
            name='introduction',
            unique_together={('content',)},
        ),
        migrations.AlterUniqueTogether(
            name='guiderevision',
            unique_together={('label',)},
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together={('label',)},
        ),
    ]
