# Generated by Django 2.0.9 on 2019-01-01 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='telegram_user_id',
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
    ]