from django.contrib import admin
from .models import Worker, Schedule


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = [
        "id", "name", "username", "work_start_time"
    ]
    search_fields = ["name"]
    list_filter = ["location", "work_start_time"]
    ordering = ["location"]


@admin.register(Schedule)
class WorkerAdmin(admin.ModelAdmin):
    list_display = [
        "id", "worker", "date", "start_time", "period_time"
    ]
    search_fields = ["worker"]
    list_filter = ["worker", "date"]
    ordering = ["date"]
