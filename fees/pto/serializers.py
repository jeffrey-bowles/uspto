from rest_framework import serializers
from .models import Patent


class PatentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patent
        fields = '__all__'
        