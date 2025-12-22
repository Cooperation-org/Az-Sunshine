"""
Authentication views for Arizona Sunshine platform
Handles registration, login, 2FA setup and verification
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
import pyotp
import qrcode
import io
import base64

from .serializers_auth import (
    RegisterSerializer,
    UserSerializer,
    TwoFactorSetupSerializer,
    TwoFactorVerifySerializer
)
from .models import UserProfile


def get_tokens_for_user(user):
    """Generate JWT tokens for user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user with admin privileges
    Auto-admin setup: First registered user becomes admin
    """
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        # Generate tokens
        tokens = get_tokens_for_user(user)

        return Response({
            'message': 'Admin account created successfully',
            'user': UserSerializer(user).data,
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login with username/password
    Returns tokens directly if 2FA is not enabled
    Returns temp token if 2FA is enabled
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({
            'error': 'Please provide both username and password'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Authenticate user
    user = authenticate(username=username, password=password)

    if not user:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Check if user has 2FA enabled
    try:
        profile = user.profile
        if profile.is_2fa_enabled:
            # Generate temporary token for 2FA verification
            temp_token = RefreshToken.for_user(user)

            return Response({
                'requires_2fa': True,
                'temp_token': str(temp_token.access_token),
                'message': 'Please enter your 6-digit code from authenticator app'
            })
    except UserProfile.DoesNotExist:
        # Create profile if doesn't exist
        profile = UserProfile.objects.create(user=user)

    # No 2FA, return full tokens
    tokens = get_tokens_for_user(user)

    return Response({
        'requires_2fa': False,
        'user': UserSerializer(user).data,
        'tokens': tokens
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def setup_2fa(request):
    """
    Generate QR code and secret for 2FA setup
    User scans QR code with Google Authenticator
    """
    user = request.user

    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=user)

    # Generate new secret if not exists or if re-setting up
    if not profile.totp_secret or request.query_params.get('regenerate'):
        profile.totp_secret = pyotp.random_base32()
        profile.save()

    # Generate TOTP URI
    totp = pyotp.TOTP(profile.totp_secret)
    issuer = "Arizona Sunshine"
    account_name = user.username

    provisioning_uri = totp.provisioning_uri(
        name=account_name,
        issuer_name=issuer
    )

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return Response({
        'secret': profile.totp_secret,
        'qr_code': f'data:image/png;base64,{img_str}',
        'issuer': issuer,
        'account_name': account_name,
        'manual_entry_key': profile.totp_secret
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enable_2fa(request):
    """
    Enable 2FA after verifying the code
    User must provide valid 6-digit code to enable
    """
    serializer = TwoFactorVerifySerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    code = serializer.validated_data['code']
    user = request.user

    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        return Response({
            'error': '2FA not set up. Please call /auth/2fa-setup/ first'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not profile.totp_secret:
        return Response({
            'error': '2FA secret not found. Please set up 2FA first'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Verify the code
    totp = pyotp.TOTP(profile.totp_secret)

    if totp.verify(code, valid_window=1):
        profile.is_2fa_enabled = True
        profile.save()

        return Response({
            'message': '2FA enabled successfully',
            'is_2fa_enabled': True
        })
    else:
        return Response({
            'error': 'Invalid code. Please try again'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_2fa(request):
    """
    Verify 2FA code after login
    Exchange temp token + code for full JWT tokens
    """
    code = request.data.get('code')
    temp_token = request.data.get('temp_token')

    if not code or not temp_token:
        return Response({
            'error': 'Please provide both code and temp_token'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Decode temp token to get user
    from rest_framework_simplejwt.tokens import AccessToken

    try:
        access_token = AccessToken(temp_token)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
    except Exception as e:
        return Response({
            'error': 'Invalid or expired temp token'
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Get user profile
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        return Response({
            'error': '2FA not enabled for this user'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not profile.is_2fa_enabled or not profile.totp_secret:
        return Response({
            'error': '2FA not enabled for this user'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Verify the code
    totp = pyotp.TOTP(profile.totp_secret)

    if totp.verify(code, valid_window=1):
        # Code is valid, generate full tokens
        tokens = get_tokens_for_user(user)

        return Response({
            'message': '2FA verification successful',
            'user': UserSerializer(user).data,
            'tokens': tokens
        })
    else:
        return Response({
            'error': 'Invalid code. Please try again'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disable_2fa(request):
    """Disable 2FA for the current user"""
    user = request.user

    try:
        profile = user.profile
        profile.is_2fa_enabled = False
        profile.totp_secret = ''
        profile.save()

        return Response({
            'message': '2FA disabled successfully',
            'is_2fa_enabled': False
        })
    except UserProfile.DoesNotExist:
        return Response({
            'error': 'User profile not found'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Get current authenticated user info"""
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user
    In JWT, logout is mainly client-side (delete tokens)
    This endpoint is for any server-side cleanup
    """
    return Response({
        'message': 'Logout successful'
    })
