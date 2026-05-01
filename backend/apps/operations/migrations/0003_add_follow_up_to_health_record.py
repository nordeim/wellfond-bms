from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('operations', '0002_add_ground_log_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='healthrecord',
            name='follow_up_date',
            field=models.DateField(
                blank=True,
                help_text='Scheduled follow-up date',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='healthrecord',
            name='follow_up_required',
            field=models.BooleanField(
                default=False,
                help_text='Whether follow-up veterinary treatment is required',
            ),
        ),
    ]