# Generated by Django 2.2.9 on 2020-02-07 03:32

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('person', '0002_person_is_validated'),
        ('beacon', '0019_auto_20200204_1510'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='attachment',
            table='beacon_attachment',
        ),
        migrations.AlterModelTable(
            name='category',
            table='beacon_category',
        ),
        migrations.AlterModelTable(
            name='chapter',
            table='beacon_chapter',
        ),
        migrations.AlterModelTable(
            name='chapterrevision',
            table='beacon_chapter_revision',
        ),
        migrations.AlterModelTable(
            name='content',
            table='beacon_content',
        ),
        migrations.AlterModelTable(
            name='explain',
            table='beacon_explain',
        ),
        migrations.AlterModelTable(
            name='explainrevision',
            table='beacon_explain_revision',
        ),
        migrations.AlterModelTable(
            name='guide',
            table='beacon_guide',
        ),
        migrations.AlterModelTable(
            name='guiderevision',
            table='beacon_guide_revision',
        ),
        migrations.AlterModelTable(
            name='introduction',
            table='beacon_introduction',
        ),
        migrations.AlterModelTable(
            name='rating',
            table='beacon_rating',
        ),
        migrations.AlterModelTable(
            name='sheet',
            table='beacon_sheet',
        ),
        migrations.AlterModelTable(
            name='sheetrevision',
            table='beacon_sheet_revision',
        ),
        migrations.AlterModelTable(
            name='tag',
            table='beacon_tag',
        ),
        migrations.AlterModelTable(
            name='vote',
            table='beacon_vote',
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('label', models.CharField(max_length=255)),
                ('slug', models.SlugField(editable=False, max_length=500)),
                ('content_blob', models.BinaryField()),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(limit_choices_to=models.Q(app_label='beacon'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('creator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='topics', to='person.Person')),
            ],
            options={
                'verbose_name': 'Discussion Topic',
                'verbose_name_plural': 'Discussion Topics',
                'db_table': 'beacon_discussion_topic',
                'abstract': False,
                'unique_together': {('label',)},
            },
        ),
        migrations.CreateModel(
            name='GuideEnrollment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('creator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='guide_enrollments', to='person.Person')),
                ('guide', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guide_enrollments', to='beacon.Guide')),
            ],
            options={
                'verbose_name': 'Guide Enrollment',
                'verbose_name_plural': 'Guide Enrollments',
                'db_table': 'beacon_enrollment_guide',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ExplainEnrollment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('date_begin', models.DateTimeField(auto_now_add=True)),
                ('date_completed', models.DateTimeField(auto_now=True)),
                ('chapter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='explain_enrollments', to='beacon.Chapter')),
                ('creator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='explain_enrollments', to='person.Person')),
                ('enrollment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='explain_enrollments', to='beacon.GuideEnrollment')),
                ('explain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='explain_enrollments', to='beacon.Explain')),
                ('guide', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='explain_enrollments', to='beacon.Guide')),
            ],
            options={
                'verbose_name': 'Explain Enrollment',
                'verbose_name_plural': 'Explain Enrollments',
                'db_table': 'beacon_enrollment_explain',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ChapterEnrollment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('chapter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chapter_enrollments', to='beacon.Chapter')),
                ('creator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chapter_enrollments', to='person.Person')),
                ('enrollment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chapter_enrollments', to='beacon.GuideEnrollment')),
                ('guide', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chapter_enrollments', to='beacon.Guide')),
            ],
            options={
                'verbose_name': 'Chapter Enrollment',
                'verbose_name_plural': 'Chapter Enrollments',
                'db_table': 'beacon_enrollment_chapter',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Reply',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('label', models.CharField(blank=True, max_length=255)),
                ('slug', models.SlugField(editable=False, max_length=500)),
                ('content_blob', models.BinaryField()),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(limit_choices_to=models.Q(app_label='beacon'), on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('creator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='replies', to='person.Person')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='beacon.Reply')),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='beacon.Topic')),
            ],
            options={
                'verbose_name': 'Discussion Reply',
                'verbose_name_plural': 'Discussion Replies',
                'db_table': 'beacon_discussion_reply',
                'abstract': False,
                'unique_together': {('label',)},
            },
        ),
    ]
