# Generated by Django 4.2.7 on 2023-12-07 14:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_import", "0011_billlading"),
    ]

    operations = [
        migrations.AddField(
            model_name="billlading",
            name="invoices",
            field=models.CharField(default="x", max_length=100),
            preserve_default=False,
        ),
    ]
