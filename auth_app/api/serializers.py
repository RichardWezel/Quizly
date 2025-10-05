from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username','password', 'confirmed_password', 'email']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'email': {
                'required': True
            }
        }

    def validate(self, attrs):
        pw = attrs.get('password')
        cpw = attrs.get('confirmed_password')

        if not pw or not cpw:
            raise serializers.ValidationError('Password and confirmation are required.')

        if pw != cpw:
            raise serializers.ValidationError('Passwords do not match.')

        attrs.pop('confirmed_password', None)
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def save(self):
        pw = self.validated_data['password']

        account = User(
            email=self.validated_data['email'], 
            username=self.validated_data['username']
        )
        account.set_password(pw)
        account.save()
        return account
    

class LoginSerializer(TokenObtainPairSerializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError('No user with this email or password found.')

        if not user.check_password(password):
            raise serializers.ValidationError('No user with this email or password found.')

        data = super().validate({"username": user.username, "password": password})

        data["user"] = {
            "id": user.pk,
            "username": user.username,
            "email": user.email,
        }
        return data