from rest_framework import serializers
from .models import AuthUser


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = AuthUser
        fields = ['id', 'name', 'email', 'password', 'role']

    def create(self, validated_data):
        user = AuthUser(
            name=validated_data['name'],
            email=validated_data['email'],
            role=validated_data.get('role', 'customer'),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = ['id', 'name', 'email', 'role', 'created_at']
