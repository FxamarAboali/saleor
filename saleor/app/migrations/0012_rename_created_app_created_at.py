# Generated by Django 3.2.12 on 2022-04-14 10:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0011_alter_apptoken_token_last_4"),
    ]

    operations = [
        migrations.RenameField(
            model_name="app",
            old_name="created",
            new_name="created_at",
        ),
    ]