# Generated by Django 3.1.6 on 2021-05-13 14:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fyle_slack_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(max_length=120)),
                ('is_enabled', models.BooleanField(default=True)),
                ('slack_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fyle_slack_app.user', to_field='slack_user_id')),
            ],
            options={
                'db_table': 'notification_preferences',
                'unique_together': {('slack_user', 'notification_type')},
            },
        ),
    ]
