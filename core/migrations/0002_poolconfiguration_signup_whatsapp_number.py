from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="poolconfiguration",
            name="signup_whatsapp_number",
            field=models.CharField(
                default="43984928377",
                help_text="Número no formato internacional ou apenas dígitos. Ex.: 5543999999999",
                max_length=20,
                verbose_name="WhatsApp para cadastro",
            ),
        ),
    ]
