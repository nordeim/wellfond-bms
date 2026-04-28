"""Add timestamps and signature fields to Sales and Signature models."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("sales", "0001_initial"),
    ]

    operations = [
        # Add completed_at and cancelled_at to SalesAgreement
        migrations.AddField(
            model_name="salesagreement",
            name="completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="salesagreement",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Add signed_by to Signature
        migrations.AddField(
            model_name="signature",
            name="signed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="signatures",
                to="core.user",
            ),
        ),
        # Add signature_data to Signature
        migrations.AddField(
            model_name="signature",
            name="signature_data",
            field=models.TextField(
                blank=True,
                help_text="Base64 encoded signature image data",
            ),
        ),
        # Add user_agent to Signature
        migrations.AddField(
            model_name="signature",
            name="user_agent",
            field=models.TextField(blank=True),
        ),
        # Add defaults for signer_type and method (already exist but ensuring defaults)
        migrations.AlterField(
            model_name="signature",
            name="signer_type",
            field=models.CharField(
                choices=[("SELLER", "Seller"), ("BUYER", "Buyer")],
                default="SELLER",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="signature",
            name="method",
            field=models.CharField(
                choices=[("IN_PERSON", "In Person"), ("REMOTE", "Remote"), ("PAPER", "Paper")],
                default="REMOTE",
                max_length=15,
            ),
        ),
    ]
