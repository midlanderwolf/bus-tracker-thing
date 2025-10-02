# Generated manually for making bearing field nullable

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0002_vehicle'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehicleposition',
            name='bearing',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Direction in degrees', max_digits=5, null=True),
        ),
    ]