"""
Authentication serializers for Arizona Sunshine platform
Handles user registration, login, and 2FA operations
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile


class RegisterSerializer(serializers.ModelSerializer):
    """User registration serializer with auto-admin setup"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs

    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """Create user with admin privileges and profile"""
        validated_data.pop('password_confirm')

        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        # Grant admin privileges
        user.is_staff = True
        user.is_superuser = True
        user.save()

        # Create profile
        UserProfile.objects.create(user=user)

        return user


class UserSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    is_2fa_enabled = serializers.BooleanField(source='profile.is_2fa_enabled', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_2fa_enabled')
        read_only_fields = ('id', 'is_staff', 'is_2fa_enabled')


class TwoFactorSetupSerializer(serializers.Serializer):
    """2FA setup response serializer"""
    secret = serializers.CharField(read_only=True)
    qr_code = serializers.CharField(read_only=True)
    issuer = serializers.CharField(read_only=True)
    account_name = serializers.CharField(read_only=True)


class TwoFactorVerifySerializer(serializers.Serializer):
    """2FA verification serializer"""
    code = serializers.CharField(
        required=True,
        min_length=6,
        max_length=6,
        help_text='6-digit code from authenticator app'
    )

    def validate_code(self, value):
        """Ensure code is numeric"""
        if not value.isdigit():
            raise serializers.ValidationError("Code must be 6 digits.")
        return value
