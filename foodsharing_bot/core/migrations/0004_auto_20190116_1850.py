# Generated by Django 2.0.9 on 2019-01-16 18:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20190101_1247'),
    ]

    operations = [
        migrations.CreateModel(
            name='Offer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(max_length=256, verbose_name='item name')),
                ('item_description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('contact_info', models.TextField(blank=True, null=True, verbose_name='contact information')),
                ('status', models.PositiveSmallIntegerField(choices=[(0, 'Receiver not assigned'), (1, 'Receiver pending'), (2, 'Receiver confirmed'), (3, 'Completed')])),
                ('photo', models.ImageField(blank=True, null=True, upload_to='photos', verbose_name='photo')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='comment')),
                ('location_name', models.CharField(max_length=500, null=True, verbose_name='location')),
                ('lat', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='latitude')),
                ('lng', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='longitude')),
            ],
        ),
        migrations.AddField(
            model_name='session',
            name='name',
            field=models.CharField(default='alex', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='offer',
            name='giver',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='given_offers', to='core.Session', verbose_name='giver'),
        ),
        migrations.AddField(
            model_name='offer',
            name='receiver',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='received_offers', to='core.Session', verbose_name='receiver'),
        ),
    ]