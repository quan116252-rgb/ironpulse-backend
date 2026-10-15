from rest_framework import serializers
from .models import ContactMessage, Trainer, GymPackage, GymClass

class GymClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymClass
        fields = '__all__'

class GymPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymPackage
        fields = '__all__'

class TrainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        fields = '__all__'

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'full_name', 'email', 'message', 'created_at']