import json
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime
from tg_bot.models import Event, User, Schedule


class Command(BaseCommand):
    help = 'Загружает тестовые данные (события, пользователей, доклады) из JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='Путь к JSON файлу с тестовыми данными'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'Файл {json_file} не найден')
        except json.JSONDecodeError:
            raise CommandError(f'Ошибка при чтении JSON из {json_file}')

        users_map = self.load_users(data.get('users', []))
        
        events_map = self.load_events(data.get('events', []))
        
        self.load_schedules(data.get('schedules', []), users_map, events_map)

        self.stdout.write(self.style.SUCCESS('Тестовые данные загружены!'))

    def load_users(self, users_data):
        users_map = {}
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                telegram_id=user_data['telegram_id'],
                defaults={
                    'telegram_username': user_data.get('telegram_username'),
                    'first_and_last_name': user_data.get('first_and_last_name'),
                    'about': user_data.get('about'),
                    'role': user_data.get('role', 'guest'),
                    'networking_profile_filled': user_data.get('networking_profile_filled', False),
                }
            )
            users_map[user_data['id']] = user
        return users_map

    def load_events(self, events_data):
        events_map = {}
        for event_data in events_data:
            date = datetime.fromisoformat(event_data['date'])
            if date.tzinfo is None:
                date = timezone.make_aware(date)
            
            event, created = Event.objects.get_or_create(
                title=event_data['title'],
                date=date,
                defaults={
                    'description': event_data.get('description', ''),
                    'location': event_data.get('location', ''),
                    'is_active': event_data.get('is_active', True),
                }
            )
            events_map[event_data['id']] = event
        return events_map

    def load_schedules(self, schedules_data, users_map, events_map):
        for schedule_data in schedules_data:
            event = events_map.get(schedule_data['event_id'])
            speaker = users_map.get(schedule_data['speaker_id'])
            
            schedule, created = Schedule.objects.update_or_create(
                event=event,
                speaker=speaker,
                order=schedule_data.get('order', 0),
                defaults={
                    'title': schedule_data.get('title', ''),
                    'description': schedule_data.get('description'),
                    'start_time': schedule_data.get('start_time'),
                    'end_time': schedule_data.get('end_time'),
                }
            )
