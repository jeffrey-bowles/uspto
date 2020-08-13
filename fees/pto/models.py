from django.db import models

# Main Patent data fields
class Patent(models.Model):
    patent_number = models.CharField(max_length=10, unique=True)
    application_number = models.CharField(max_length=10)
    entity_status = models.CharField(max_length=1)
    application_date = models.DateField()
    issue_date = models.DateField()
    reel_num = models.CharField(max_length=10, blank=True, null=True)
    frame_num = models.CharField(max_length=10, blank=True, null=True)
    correspondent_name = models.CharField(max_length=255, blank=True, null=True)
    correspondent_address = models.TextField(blank=True, null=True)
    pat_assignee_name = models.CharField(max_length=255, blank=True, null=True)
    pat_assignee_address = models.TextField(blank=True, null=True)
    class Meta:
        verbose_name_plural = 'Patents'

# Unique Maintenance Fee Events
class FeeEvents(models.Model):
    patent = models.ForeignKey(
    	   Patent,
    	   on_delete=models.CASCADE
    )
    maintenance_date = models.DateField()
    maintenance_code = models.CharField(max_length=5)
    class Meta:
        verbose_name_plural = "Maintenance Fee Events"
