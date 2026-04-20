"""
Background Scheduler
=====================
Uses APScheduler to periodically check for duties that should be
auto-completed (past their scheduled end time).
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from models import event as event_model
from models import substitution as sub_model
from models import notification as notif_model


scheduler = BackgroundScheduler()


def check_and_complete_duties():
    """
    Check for duties that have passed their end time and mark them completed.
    Also completes associated substitutions and sends notifications.
    """
    try:
        events = event_model.get_events_to_complete()
        for event in events:
            # Mark event as completed
            event_model.update_event_status(event['id'], 'completed')
            
            # Complete associated substitutions
            sub_model.complete_substitutions_by_event(event['id'])
            
            # Notify the assigned faculty
            notif_model.create_notification(
                user_id=event['assigned_faculty_id'],
                title='Duty Completed',
                message=f'Your duty "{event["event_name"]}" has been marked as completed.',
                notif_type='completion'
            )
            
            # Notify substitute faculty
            subs = sub_model.get_substitutions_by_event(event['id'])
            for sub in subs:
                notif_model.create_notification(
                    user_id=sub['substitute_faculty_id'],
                    title='Substitution Completed',
                    message=f'Your substitution for {sub["subject"]} in {sub["classroom"]} has been completed.',
                    notif_type='completion'
                )
            
            print(f"[Scheduler] Auto-completed duty #{event['id']}: {event['event_name']}")
    except Exception as e:
        print(f"[Scheduler] Error checking duties: {e}")


def init_scheduler(app):
    """Initialize and start the background scheduler."""
    from config import Config
    
    scheduler.add_job(
        func=check_and_complete_duties,
        trigger='interval',
        seconds=Config.SCHEDULER_INTERVAL_SECONDS,
        id='duty_completion_checker',
        name='Check and complete past duties',
        replace_existing=True
    )
    
    if not scheduler.running:
        scheduler.start()
        print(f"[✓] Background scheduler started (interval: {Config.SCHEDULER_INTERVAL_SECONDS}s)")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[✓] Scheduler shutdown.")
