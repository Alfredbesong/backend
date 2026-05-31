from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from rest_framework import serializers

from .models import DeviceToken

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone_number', 'profile_photo']


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9\s()-]{7,20}$',
                message='Enter a valid phone number.',
            )
        ],
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'role', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Username is required.')
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        if not value:
            raise serializers.ValidationError('Email is required.')
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('This email is already in use.')
        return value

    def validate_first_name(self, value):
        return value.strip()

    def validate_last_name(self, value):
        return value.strip()

    def validate_phone_number(self, value):
        return value.strip()

    def validate_password(self, value):
        validate_password(value, user=User())
        return value

    def validate(self, attrs):
        attrs['username'] = attrs.get('username', '').strip()
        attrs['email'] = attrs.get('email', '').strip().lower()
        attrs['first_name'] = attrs.get('first_name', '').strip()
        attrs['last_name'] = attrs.get('last_name', '').strip()
        attrs['phone_number'] = attrs.get('phone_number', '').strip()
        return attrs


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['token', 'platform']

    def validate_token(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Device token is required.')
        return value


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    remove_profile_photo = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'profile_photo',
            'remove_profile_photo',
        ]

    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Username is required.')
        if User.objects.filter(username__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        if not value:
            raise serializers.ValidationError('Email is required.')
        if User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('This email is already in use.')
        return value

    def validate_first_name(self, value):
        return value.strip()

    def validate_last_name(self, value):
        return value.strip()

    def validate_phone_number(self, value):
        return value.strip()

    def update(self, instance, validated_data):
        remove_profile_photo = validated_data.pop('remove_profile_photo', False)
        profile_photo = validated_data.pop('profile_photo', None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if remove_profile_photo and instance.profile_photo:
            instance.profile_photo.delete(save=False)
            instance.profile_photo = None

        if profile_photo is not None:
            if instance.profile_photo:
                instance.profile_photo.delete(save=False)
            instance.profile_photo = profile_photo

        instance.save()
        return instance
