from django.contrib import admin
from tg_bot.models import Event, User, Schedule, Question, MatchHistory, NetworkingProfile


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'location', 'current_speaker', 'is_active')
    list_filter = ('is_active', 'date')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('first_and_last_name', 'telegram_id', 'role', 'networking_profile_filled')
    list_filter = ('role', 'networking_profile_filled', 'created_at')
    search_fields = ('first_and_last_name', 'telegram_id', 'telegram_username')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('events',)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('event', 'speaker', 'title', 'start_time', 'end_time', 'order')
    list_filter = ('event', 'start_time')
    search_fields = ('title', 'speaker__first_and_last_name')
    ordering = ('event', 'order')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('speaker', 'sender', 'is_answered', 'created_at')
    list_filter = ('is_answered', 'created_at', 'event')
    search_fields = ('text', 'answer', 'sender__first_and_last_name', 'speaker__first_and_last_name')
    readonly_fields = ('created_at', 'answered_at')


@admin.register(MatchHistory)
class MatchHistoryAdmin(admin.ModelAdmin):
    list_display = ('event', 'initiator', 'target', 'accepted', 'skipped', 'created_at')
    list_filter = ('event', 'accepted', 'skipped', 'created_at')
    search_fields = ('initiator__first_and_last_name', 'target__first_and_last_name')


@admin.register(NetworkingProfile)
class NetworkingProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'created_at')
    list_filter = ('event', 'created_at')
    search_fields = ('user__first_and_last_name', 'about')