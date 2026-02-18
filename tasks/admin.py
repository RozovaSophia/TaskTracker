from django.contrib import admin
from .models import Task, Comment, Tag


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "priority", "author", "assignee", "deadline")
    list_filter = ("status", "priority", "created_at")
    search_fields = ("title", "description")
    raw_id_fields = ("author", "assignee")
    date_hierarchy = "created_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "created_at")
    list_filter = ("created_at",)
    raw_id_fields = ("task", "author")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
