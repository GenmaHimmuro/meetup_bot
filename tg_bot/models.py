from django.db import models
from django.utils import timezone


class Event(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    date = models.DateTimeField(verbose_name="Дата и время")
    location = models.CharField(max_length=255, verbose_name="Место проведения")
    
    current_speaker = models.ForeignKey(
        'User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='current_speaker_at',
        verbose_name="Текущий докладчик"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Активное мероприятие")
    
    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.title} ({self.date.strftime('%d.%m.%Y')})"
    
    @property
    def is_happening_now(self):
        now = timezone.now()
        return self.date <= now <= (self.date.replace(hour=self.date.hour + 4))


class User(models.Model):
    ROLE_CHOICES = [
        ('guest', 'Гость'),
        ('speaker', 'Докладчик'),
        ('organizer', 'Организатор'),
    ]
    
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    telegram_username = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Telegram username"
    )
    first_and_last_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Имя и фамилия")
    
    about = models.TextField(
        null=True,
        blank=True,
        max_length=200,
        verbose_name="О себе (стек, опыт, интересы)"
    )
    networking_profile_filled = models.BooleanField(
        default=False,
        verbose_name="Анкета нетворкинга заполнена"
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='guest',
        verbose_name="Роль"
    )
    
    events = models.ManyToManyField(Event, blank=True, verbose_name="Мероприятия")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_and_last_name} ({self.telegram_id})"


class Schedule(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='schedule')
    speaker = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Докладчик")
    title = models.CharField(max_length=255, verbose_name="Название доклада")
    description = models.TextField(null=True, blank=True, verbose_name="Описание доклада")
    
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")
    
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок выступления")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "График выступлений"
        verbose_name_plural = "Графики выступлений"
        ordering = ['event', 'order']
        unique_together = ('event', 'speaker', 'order')
    
    def __str__(self):
        return f"{self.event} - {self.title}"


class Question(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='questions')
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_questions',
        verbose_name="Автор вопроса"
    )
    speaker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_questions',
        verbose_name="Докладчик"
    )
    
    text = models.TextField(max_length=500, verbose_name="Текст вопроса")
    answer = models.TextField(
        null=True,
        blank=True,
        verbose_name="Ответ спикера"
    )
    
    is_read = models.BooleanField(default=False, verbose_name="Прочитано спикером")
    is_answered = models.BooleanField(default=False, verbose_name="Получен ответ")
    
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name="Время ответа")
    
    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Вопрос от {self.sender.first_and_last_name} спикеру {self.speaker.first_and_last_name}"


class NetworkingProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='networking_profile')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    
    name = models.CharField(max_length=255, verbose_name="Имя")
    about = models.TextField(max_length=200, verbose_name="О себе")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Профиль нетворкинга"
        verbose_name_plural = "Профили нетворкинга"
        unique_together = ('user', 'event')
    
    def __str__(self):
        return f"{self.user.first_and_last_name} ({self.event.title})"


class MatchHistory(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    initiator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_matches')
    target = models.ForeignKey(User, on_delete=models.CASCADE, related_name='target_matches')
    
    accepted = models.BooleanField(default=False, verbose_name="Принято")
    skipped = models.BooleanField(default=False, verbose_name="Пропущено")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "История матчей"
        verbose_name_plural = "Истории матчей"
        unique_together = ('event', 'initiator', 'target')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.initiator.first_and_last_name} ↔ {self.target.first_and_last_name}"
