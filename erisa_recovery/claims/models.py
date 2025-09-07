from django.db import models
from django.contrib.auth.models import User


class Claim(models.Model):
    id = models.IntegerField(primary_key=True)
    patient_name = models.CharField(max_length=200)
    billed_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=50, default="Pending")
    insurer_name = models.CharField(max_length=200)
    discharge_date = models.DateField()
    flagged = models.BooleanField(default=False)

    def __str__(self):
        return f"Claim {self.id} - {self.patient_name}"



class ClaimDetail(models.Model):
    claim = models.OneToOneField(Claim, on_delete=models.CASCADE, related_name="detail")
    denial_reason = models.CharField(max_length=255)
    cpt_codes = models.CharField(max_length=255)

    def __str__(self):
        return f"Detail for Claim {self.claim_id}"


class Note(models.Model):
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)