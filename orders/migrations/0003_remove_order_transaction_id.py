# Generated by Django 5.0.6 on 2024-05-26 17:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_order_transaction_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='transaction_id',
        ),
    ]