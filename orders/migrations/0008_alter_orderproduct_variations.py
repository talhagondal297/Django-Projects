# Generated by Django 5.0.6 on 2024-05-27 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_remove_orderproduct_variation_and_more'),
        ('store', '0004_alter_reviewrating_updated_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderproduct',
            name='variations',
            field=models.ManyToManyField(blank=True, to='store.variation'),
        ),
    ]
