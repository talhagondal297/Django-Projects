# Generated by Django 5.0.6 on 2024-05-27 13:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0010_remove_order_grand_total'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderproduct',
            name='color',
        ),
        migrations.RemoveField(
            model_name='orderproduct',
            name='size',
        ),
    ]