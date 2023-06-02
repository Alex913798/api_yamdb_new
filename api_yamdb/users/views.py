from django.shortcuts import get_object_or_404


from rest_framework import generics, status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action

from .models import User
from .perrmissions import IsAdmin
from .serializers import SignUpSerializer, TokenSerializer, UsersSerializer


class SignUpView(generics.CreateAPIView):
    serializer_class = SignUpSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        email = serializer.validated_data['email']
        username = serializer.validated_data['username']
        existing_user = User.objects.filter(email=email,
                                            username=username,).first()
        if existing_user:
            response_data = {
                'email': existing_user.email,
                'username': existing_user.username,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        response_data = {
            'email': user.email,
            'username': user.username,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class TokenView(APIView):
    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class UsersView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    permission_classes = [IsAdmin]
    filter_backends = [SearchFilter]
    search_fields = ('username',)

    def retrieve(self, request, pk=None):
        username = self.kwargs[self.lookup_field]
        instance = get_object_or_404(User, username=username)
        return Response(self.serializer_class(instance).data,
                        status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        return self.http_method_not_allowed(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        username = self.kwargs[self.lookup_field]
        user = get_object_or_404(User, username=username)
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        username = self.kwargs[self.lookup_field]
        user = get_object_or_404(User, username=username)
        self.perform_destroy(user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['get', 'patch'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        request_data = request.data.copy()
        if 'role' in request.data:
            request_data['role'] = request.user.role
        serializer = self.get_serializer(user, data=request_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
