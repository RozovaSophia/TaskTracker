from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Comment, Tag


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей"""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для комментариев"""

    author_name = serializers.ReadOnlyField(source="author.username")

    class Meta:
        model = Comment
        fields = [
            "id",
            "text",
            "author",
            "author_name",
            "task",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["author", "created_at", "updated_at"]

    def validate(self, data):
        """Проверяем, что task передан"""
        if "task" not in data:
            raise serializers.ValidationError({"task": "Это поле обязательно"})
        return data


class TaskSerializer(serializers.ModelSerializer):
    """Сериализатор для задач"""

    author_name = serializers.ReadOnlyField(source="author.username")
    assignee_name = serializers.ReadOnlyField(source="assignee.username")
    comments = CommentSerializer(many=True, read_only=True)
    comments_count = serializers.IntegerField(source="comments.count", read_only=True)
    tags = serializers.SlugRelatedField(
        many=True, slug_field="name", queryset=Tag.objects.all(), required=False
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "created_at",
            "updated_at",
            "deadline",
            "completed_at",
            "author",
            "author_name",
            "assignee",
            "assignee_name",
            "comments",
            "comments_count",
            "tags",
        ]
        read_only_fields = ["author", "created_at", "updated_at", "completed_at"]

    def validate_deadline(self, value):
        """Проверка, что дедлайн не в прошлом"""
        from django.utils import timezone

        if value and value < timezone.now():
            raise serializers.ValidationError("Дедлайн не может быть в прошлом")
        return value


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов"""

    tasks_count = serializers.IntegerField(source="tasks.count", read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "color", "tasks_count"]
