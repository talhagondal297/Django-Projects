# Generated by Django 5.0.6 on 2024-05-27 12:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_order_grand_total'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='grand_total',
        ),
    ]