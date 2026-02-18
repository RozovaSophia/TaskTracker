from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from datetime import datetime, timedelta
from .models import Task, Comment, Tag


class CommentAPITest(TestCase):
    """Тесты для API комментариев"""

    def setUp(self):
        Comment.objects.all().delete()
        Task.objects.all().delete()
        User.objects.all().delete()

        self.client = APIClient()

        self.user = User.objects.create_user(username="testuser", password="testpass")

        self.task = Task.objects.create(
            title="Тестовая задача",
            description="Описание",
            author=self.user,
            assignee=self.user,
        )

        self.comment = Comment.objects.create(
            task=self.task, author=self.user, text="Тестовый комментарий"
        )

        self.comments_url = reverse("comment-list")

    def test_list_comments(self):
        """Тест получения списка комментариев"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.comments_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if "results" in response.data:
            self.assertEqual(len(response.data["results"]), 1)
        else:
            self.assertEqual(len(response.data), 1)

    def test_create_comment(self):
        """Тест создания комментария"""
        self.client.force_authenticate(user=self.user)

        self.assertTrue(Task.objects.filter(id=self.task.id).exists())

        comment_data = {"task": self.task.id, "text": "Новый комментарий"}

        print(f"POST to {self.comments_url}")
        print(f"Data: {comment_data}")

        response = self.client.post(self.comments_url, comment_data, format="json")

        print(f"Status code: {response.status_code}")
        print(f"Response data: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author_name"], self.user.username)


class TagAPITest(TestCase):
    """Тесты для API тегов"""

    def setUp(self):
        Tag.objects.all().delete()
        User.objects.all().delete()

        self.client = APIClient()

        self.user = User.objects.create_user(username="testuser", password="testpass")

        self.tag = Tag.objects.create(name="Тестовый тег", color="#FF0000")

        self.tags_url = reverse("tag-list")

    def test_list_tags(self):
        """Тест получения списка тегов"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.tags_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if "results" in response.data:
            self.assertEqual(len(response.data["results"]), 1)
        else:
            self.assertEqual(len(response.data), 1)

    def test_search_tags(self):
        """Тест поиска тегов"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.tags_url, {"search": "тестовый"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if "results" in response.data:
            self.assertEqual(len(response.data["results"]), 1)
            self.assertEqual(response.data["results"][0]["name"], "Тестовый тег")
        else:
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]["name"], "Тестовый тег")


class TaskAPITest(TestCase):
    """Тесты для API задач"""

    def setUp(self):
        Task.objects.all().delete()
        User.objects.all().delete()
        Comment.objects.all().delete()

        self.client = APIClient()

        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")
        self.admin = User.objects.create_superuser(
            username="admin", password="admin123", email="admin@example.com"
        )

        self.task1 = Task.objects.create(
            title="Задача пользователя 1",
            description="Описание задачи 1",
            author=self.user1,
            assignee=self.user1,
        )

        self.task2 = Task.objects.create(
            title="Задача пользователя 2",
            description="Описание задачи 2",
            author=self.user2,
            assignee=self.user2,
        )

        self.task3 = Task.objects.create(
            title="Общая задача",
            description="Исполнитель user2, автор user1",
            author=self.user1,
            assignee=self.user2,
        )

        # URL'ы
        self.tasks_url = reverse("task-list")

    def test_list_tasks_authenticated(self):
        """Тест: авторизованный пользователь видит свои задачи"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.tasks_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tasks = (
            response.data["results"] if "results" in response.data else response.data
        )
        self.assertEqual(len(tasks), 2)

    def test_user_sees_only_own_tasks(self):
        """Тест: user2 видит только свои задачи"""
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.tasks_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tasks = (
            response.data["results"] if "results" in response.data else response.data
        )
        self.assertEqual(len(tasks), 2)

    def test_update_task_by_non_author(self):
        """Тест: не автор не может обновить задачу"""
        self.client.force_authenticate(user=self.user2)

        task_detail_url = reverse("task-detail", args=[self.task1.id])
        response = self.client.patch(task_detail_url, {"title": "Попытка взлома"})

        self.assertIn(
            response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )

    def test_add_comment_to_foreign_task(self):
        """Тест: нельзя комментировать чужую задачу"""
        self.client.force_authenticate(user=self.user2)

        comment_url = reverse("task-add-comment", args=[self.task1.id])
        comment_data = {"text": "Попытка комментария"}

        response = self.client.post(comment_url, comment_data, format="json")
        self.assertIn(
            response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )

    def test_admin_sees_all_tasks(self):
        """Тест: админ видит все задачи"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.tasks_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tasks = (
            response.data["results"] if "results" in response.data else response.data
        )
        self.assertEqual(len(tasks), 3)  # Должно быть 3 задачи
