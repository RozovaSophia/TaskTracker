from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Task(models.Model):
    """ Модель задачи"""

    class Status(models.TextChoices):
        TODO = "TODO", "К выполнению"
        IN_PROGRESS = "IN_PROGRESS", "В работе"
        DONE = "DONE", "Выполнено"
        ARCHIVED = "ARCHIVED", "В архиве"

    class Priority(models.TextChoices):
        LOW = "LOW", "Низкий"
        MEDIUM = "MEDIUM", "Средний"
        HIGH = "HIGH", "Высокий"
        CRITICAL = "CRITICAL", "Критический"

    title = models.CharField("Заголовок", max_length=255)
    description = models.TextField("Описание", blank=True)

    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices, default=Status.TODO
    )
    priority = models.CharField(
        "Приоритет", max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )

    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    deadline = models.DateTimeField("Срок выполнения", null=True, blank=True)
    completed_at = models.DateTimeField("Дата выполнения", null=True, blank=True)

    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="authored_tasks",
        verbose_name="Автор",
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        verbose_name="Исполнитель",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["deadline"]),
            models.Index(fields=["author", "status"]),
        ]

    def __str__(self):
        return f"{self.title} (автор: {self.author.username})"

    def save(self, *args, **kwargs):
        if self.status == self.Status.DONE and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != self.Status.DONE and self.completed_at:
            self.completed_at = None
        super().save(*args, **kwargs)


class Comment(models.Model):
    """ Модель комментария к задаче """

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="comments", verbose_name="Задача"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments", verbose_name="Автор"
    )
    text = models.TextField("Текст комментария")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ["created_at"]

    def __str__(self):
        return f"Комментарий {self.author.username} к {self.task.title}"


class Tag(models.Model):
    """
    Теги для задач (для демонстрации ManyToMany связи)
    """

    name = models.CharField("Название", max_length=50, unique=True)
    color = models.CharField("Цвет", max_length=7, default="#007bff")
    tasks = models.ManyToManyField(Task, related_name="tags", blank=True)

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name
