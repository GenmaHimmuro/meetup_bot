from django.utils import timezone
from django.db.models import Q
from asgiref.sync import sync_to_async
from datetime import datetime, time

from tg_bot.models import Event, User, Schedule, Question, NetworkingProfile, MatchHistory


class DatabaseHandler:
    @staticmethod
    @sync_to_async
    def get_or_create_user(telegram_id, telegram_username=None):
        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={'telegram_username': telegram_username, 'role': 'guest'}
        )
        return user

    @staticmethod
    @sync_to_async
    def update_user_profile(telegram_id, first_and_last_name, about):
        user = User.objects.filter(telegram_id=telegram_id).first()
        if user:
            user.first_and_last_name = first_and_last_name
            user.about = about
            user.save(update_fields=['first_and_last_name', 'about'])
            return user
        return None

    @staticmethod
    @sync_to_async
    def set_user_role(telegram_id, role):
        user = User.objects.filter(telegram_id=telegram_id).first()
        if user and role in ['guest', 'speaker', 'organizer']:
            user.role = role
            user.save(update_fields=['role'])
            return user
        return None

    @staticmethod
    @sync_to_async
    def get_user_by_telegram_id(telegram_id):
        return User.objects.filter(telegram_id=telegram_id).first()
    
    @staticmethod
    @sync_to_async
    def get_user_by_id(user_id: int):
        return User.objects.filter(id=user_id).first()

    @staticmethod
    @sync_to_async
    def mark_networking_filled(telegram_id):
        user = User.objects.filter(telegram_id=telegram_id).first()
        if user:
            user.networking_profile_filled = True
            user.save(update_fields=['networking_profile_filled'])
            return user
        return None

    @staticmethod
    @sync_to_async
    def get_active_events():
        return list(Event.objects.filter(is_active=True).order_by('-date'))
    
    @staticmethod
    @sync_to_async
    def get_non_active_events():
        return list(Event.objects.filter(is_active=False).order_by('-date'))

    @staticmethod
    @sync_to_async
    def get_event_by_id(event_id):
        return Event.objects.filter(id=event_id).first()

    @staticmethod
    @sync_to_async
    def get_happening_now_event():
        now = timezone.now()
        events = Event.objects.filter(
            is_active=True,
            date__lte=now
        ).order_by('-date')
        for event in events:
            if event.is_happening_now:
                return event
        return None

    @staticmethod
    @sync_to_async
    def add_user_to_event(telegram_id, event_id):
        user = User.objects.filter(telegram_id=telegram_id).first()
        event = Event.objects.filter(id=event_id).first()
        if user and event:
            user.events.add(event)
            return True
        return False

    @staticmethod
    @sync_to_async
    def remove_user_from_event(telegram_id, event_id):
        user = User.objects.filter(telegram_id=telegram_id).first()
        event = Event.objects.filter(id=event_id).first()
        if user and event:
            user.events.remove(event)
            return True
        return False

    @staticmethod
    @sync_to_async
    def is_user_on_event(telegram_id, event_id):
        user = User.objects.filter(telegram_id=telegram_id).first()
        if user:
            return user.events.filter(id=event_id).exists()
        return False

    @staticmethod
    @sync_to_async
    def get_event_schedule(event_id):
        return list(
        Schedule.objects.filter(event_id=event_id)
        .select_related('speaker')  
        .order_by('order')
    )

    @staticmethod
    @sync_to_async
    def get_speaker_schedule(speaker_id, event_id):
        return list(
        Schedule.objects.filter(
            event_id=event_id,
            speaker_id=speaker_id
        )
        .select_related('speaker')
        .order_by('start_time')
    )

    @staticmethod
    @sync_to_async
    def get_current_speaker(event_id):
        now = timezone.localtime()
        current_speaker = Schedule.objects.filter(
                event_id=event_id,
                start_time__lte=now.time(),
                end_time__gt=now.time()
            ).order_by('order').first()
        return current_speaker.speaker

    @staticmethod
    @sync_to_async
    def get_speakers_for_event(event_id):
        speakers = User.objects.filter(
            schedule__event_id=event_id
        ).distinct()
        return list(speakers)

    @staticmethod
    @sync_to_async
    def create_schedule_entry(event_id, speaker_id, title, description, 
                              start_time, end_time, order):
        try:
            schedule = Schedule.objects.create(
                event_id=event_id,
                speaker_id=speaker_id,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                order=order
            )
            return schedule
        except Exception as e:
            return None

    @staticmethod
    @sync_to_async
    def get_speaker_questions(telegram_id, event_id):
        user = User.objects.filter(telegram_id=telegram_id).first()
        
        questions = list(
            Question.objects.filter(
                speaker_id=user.id,
                event_id=event_id
            )
            .select_related('sender', 'speaker')
            .order_by('-created_at')
        )
        
        return questions

        
    @staticmethod
    @sync_to_async
    def get_unanswered_questions(speaker_id, event_id):
        return list(
            Question.objects.filter(
                speaker_id=speaker_id,
                event_id=event_id,
                is_answered=False
            )
            .select_related('sender', 'speaker')
            .order_by('-created_at')
        )

    @staticmethod
    @sync_to_async
    def save_question(event_id, sender_telegram_id, speaker_telegram_id, text):
        try:
            sender, _ = User.objects.get_or_create(
                telegram_id=sender_telegram_id,
                defaults={'role': 'guest'}
            )
            
            speaker = User.objects.filter(telegram_id=speaker_telegram_id).first()
            if not speaker:
                print(f"Speaker not found: {speaker_telegram_id}")
                return None
            
            question = Question.objects.create(
                event_id=event_id,
                sender_id=sender.id,
                speaker_id=speaker.id,
                text=text
            )
            return question
        except Exception as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    @sync_to_async
    def save_answer(question_id, answer):
        question = Question.objects.filter(id=question_id).first()
        if question:
            question.answer = answer
            question.is_answered = True
            question.answered_at = timezone.now()
            question.save(update_fields=['answer', 'is_answered', 'answered_at'])
            return question
        return None

    @staticmethod
    @sync_to_async
    def get_question_by_id(question_id):
        return (
            Question.objects
            .filter(id=question_id)
            .select_related('sender', 'speaker')
            .first()
        )

    @staticmethod
    @sync_to_async
    def mark_question_read(question_id):
        question = Question.objects.filter(id=question_id).first()
        if question:
            question.is_read = True
            question.save(update_fields=['is_read'])
            return question
        return None

    @staticmethod
    @sync_to_async
    def get_networking_profile(user_id, event_id):
        return NetworkingProfile.objects.filter(
            user_id=user_id,
            event_id=event_id
        ).first()

    @staticmethod
    @sync_to_async
    def save_networking_profile(telegram_id, event_id, name, about):
        user = User.objects.filter(telegram_id=telegram_id).first()
        if not user:
            return None
        
        profile, created = NetworkingProfile.objects.get_or_create(
            user_id=user.id,
            event_id=event_id,
            defaults={'name': name, 'about': about}
        )
        if not created:
            profile.name = name
            profile.about = about
            profile.save(update_fields=['name', 'about'])
        return profile
    
    @staticmethod
    @sync_to_async
    def get_other_profiles(user_id, event_id):
        profiles = NetworkingProfile.objects.filter(
            event_id=event_id
        ).exclude(user_id=user_id)
        return list(profiles)

    @staticmethod
    @sync_to_async
    def save_match_history(event_id, initiator_id, target_id, accepted=False, skipped=False):
        try:
            match, created = MatchHistory.objects.get_or_create(
                event_id=event_id,
                initiator_id=initiator_id,
                target_id=target_id,
                defaults={'accepted': accepted, 'skipped': skipped}
            )
            if not created:
                match.accepted = accepted
                match.skipped = skipped
                match.save(update_fields=['accepted', 'skipped'])
            return match
        except Exception:
            return None

    @staticmethod
    @sync_to_async
    def get_users_on_event(event_id):
        event = Event.objects.filter(id=event_id).first()
        return list(event.user_set.all())
    
    @staticmethod
    @sync_to_async
    def get_organizers_telegram_ids():
        organizers = User.objects.filter(role='organizer').values_list('telegram_id', flat=True)
        return list(organizers)
    
    @staticmethod
    @sync_to_async
    def get_guests_and_speakers_telegram_ids():
        guests_and_speakers = User.objects.filter(
            Q(role='guest') | Q(role='speaker')
        ).values_list('telegram_id', flat=True)
        return list(guests_and_speakers)
    
    @staticmethod
    @sync_to_async
    def update_schedule_time(schedule_id, start_time_str, end_time_str):
        start_time_obj = datetime.strptime(start_time_str, "%H:%M").time()
        end_time_obj = datetime.strptime(end_time_str, "%H:%M").time()
        schedule = Schedule.objects.filter(id=schedule_id).first()
        if not schedule:
            return False
        schedule.start_time = start_time_obj
        schedule.end_time = end_time_obj
        schedule.save(update_fields=['start_time', 'end_time'])
        return True
    
    @staticmethod
    @sync_to_async
    def get_next_profile_for_matching(user_id: int, event_id: int):
        return NetworkingProfile.objects.filter(
            event_id=event_id
        ).exclude(user_id=user_id).first()


db = DatabaseHandler()