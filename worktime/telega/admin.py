from django.contrib import admin
from .models import Worker


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = [
        "id", "name", "username", "work_start_time"
    ]
    search_fields = ["name"]
    list_filter = ["location", "work_start_time"]
    ordering = ["location"]
