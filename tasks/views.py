from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.db import models
from .models import Task, Comment, Tag
from .serializers import (
    TaskSerializer,
    CommentSerializer,
    TagSerializer,
    UserSerializer,
)


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение на редактирование только автору
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.author == request.user


class IsAssigneeOrAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение на просмотр - исполнитель или автор
    """

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user or obj.assignee == request.user


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet для задач
    """

    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "priority"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "deadline", "priority"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Пользователи видят только свои задачи и задачи, где они исполнители
        """
        user = self.request.user

        if user.is_superuser:
            return Task.objects.all()

        return Task.objects.filter(
            models.Q(author=user) | models.Q(assignee=user)
        ).distinct()

    def perform_create(self, serializer):
        """Автором задачи становится текущий пользователь"""
        serializer.save(author=self.request.user)

    def get_permissions(self):
        """
        Настройка прав для разных действий
        """
        if self.action in ["update", "partial_update", "destroy"]:
            self.permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
        elif self.action in ["retrieve", "list"]:
            self.permission_classes = [
                permissions.IsAuthenticated,
                IsAssigneeOrAuthorOrReadOnly,
            ]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def add_comment(self, request, pk=None):
        """Добавление комментария к задаче"""
        task = self.get_object()

        if not (task.author == request.user or task.assignee == request.user):
            return Response(
                {"error": "Вы можете комментировать только свои задачи"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(task=task, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        """Изменение статуса задачи"""
        task = self.get_object()

        if not (task.author == request.user or task.assignee == request.user):
            return Response(
                {"error": "Только автор или исполнитель могут менять статус"},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_status = request.data.get("status")

        if new_status not in dict(Task.Status.choices):
            return Response(
                {"error": "Некорректный статус"}, status=status.HTTP_400_BAD_REQUEST
            )

        task.status = new_status
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для комментариев
    """

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Пользователи видят комментарии только к своим задачам"""
        user = self.request.user
        if user.is_superuser:
            return Comment.objects.all()

        return Comment.objects.filter(
            models.Q(task__author=user) | models.Q(task__assignee=user)
        ).distinct()

    def perform_create(self, serializer):
        print("Request data:", self.request.data)
        print("Task ID:", self.request.data.get("task"))

        # Сохраняем комментарий с автором
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet для тегов (доступны всем аутентифицированным)
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра пользователей
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email", "first_name", "last_name"]


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet для тегов (доступны всем аутентифицированным)
    """

    queryset = Tag.objects.all().order_by("name")  # Добавь order_by
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
