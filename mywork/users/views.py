from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render

from .models import Profile, CollaborationRequest
from .serializers import ProfileSerializer, CollaborationRequestSerializer, UserSerializer


User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        role = request.data.get('role')

        if not all([username, email, password, role]):
            return Response({'detail': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        if role not in ['investor', 'entrepreneur']:
            return Response({'detail': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'detail': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'detail': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password, role=role)

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'role': user.role,
            'username': user.username,
            'email': user.email,
        }, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    def post(self, request):
        username_or_email = request.data.get('email') or request.data.get('username')
        password = request.data.get('password')

        if not all([username_or_email, password]):
            return Response({'detail': 'Missing credentials'}, status=status.HTTP_400_BAD_REQUEST)

        # Try authenticating with username first
        user = authenticate(request, username=username_or_email, password=password)
        if user is None:
            # Try authenticating by resolving email to username
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is None:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'role': user.role,
            'username': user.username,
            'email': user.email,
        })


class ProfileDetailView(APIView):
    def get(self, request, id):
        user = get_object_or_404(User, id=id)
        profile, _ = Profile.objects.get_or_create(user=user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)


class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def put(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        allowed_fields = {
            'bio',
            'startup_name', 'startup_description', 'funding_need', 'pitch_deck_url',
            'investment_interests', 'portfolio_companies'
        }
        data = {k: v for k, v in request.data.items() if k in allowed_fields}
        for field, value in data.items():
            setattr(profile, field, value)
        profile.save()
        return Response(ProfileSerializer(profile).data)


class EntrepreneursListView(APIView):
    def get(self, request):
        users = User.objects.filter(role='entrepreneur')
        # Ensure profile exists for each
        profiles = [Profile.objects.get_or_create(user=u)[0] for u in users]
        serializer = ProfileSerializer(profiles, many=True)
        return Response(serializer.data)


class InvestorsListView(APIView):
    def get(self, request):
        users = User.objects.filter(role='investor')
        profiles = [Profile.objects.get_or_create(user=u)[0] for u in users]
        serializer = ProfileSerializer(profiles, many=True)
        return Response(serializer.data)


class CollaborationRequestCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        role = getattr(request.user, 'role', None)
        if role != 'investor':
            return Response({'detail': 'Only investors can send requests'}, status=status.HTTP_403_FORBIDDEN)
        entrepreneur_id = request.data.get('entrepreneur_id')
        message = request.data.get('message', '')
        if not entrepreneur_id:
            return Response({'detail': 'entrepreneur_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            entrepreneur = User.objects.get(id=entrepreneur_id, role='entrepreneur')
        except User.DoesNotExist:
            return Response({'detail': 'Entrepreneur not found'}, status=status.HTTP_404_NOT_FOUND)
        collab = CollaborationRequest.objects.create(
            investor=request.user,
            entrepreneur=entrepreneur,
            message=message
        )
        return Response(CollaborationRequestSerializer(collab).data, status=status.HTTP_201_CREATED)


class CollaborationRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == 'investor':
            qs = CollaborationRequest.objects.filter(investor=user)
        else:
            qs = CollaborationRequest.objects.filter(entrepreneur=user)
        return Response(CollaborationRequestSerializer(qs, many=True).data)


class CollaborationRequestUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def patch(self, request, id):
        collab = get_object_or_404(CollaborationRequest, id=id)
        # Only the entrepreneur recipient can update status
        if request.user != collab.entrepreneur:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        status_value = request.data.get('status')
        if status_value not in ['Accepted', 'Rejected']:
            return Response({'detail': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        collab.status = status_value
        collab.save()
        return Response(CollaborationRequestSerializer(collab).data)


def chat_view(request, user_id):
    return render(request, 'chat.html')


def chat_simple_view(request, user_id):
    return render(request, 'chat_simple.html')
