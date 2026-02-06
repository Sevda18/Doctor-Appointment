from app.models.notification import Notification

def create_notification(db, user_id: int, message: str):
    notif = Notification(user_id=user_id, message=message)
    db.add(notif)