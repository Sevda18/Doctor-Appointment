from app.db import SessionLocal
from app.models.user import User
from app.core.security import hash_password

db = SessionLocal()

email = "admin@local"
password = "admin123"

exists = db.query(User).filter(User.email == email).first()
if not exists:
    admin = User(email=email, username="admin", password_hash=hash_password(password), role="ADMIN")
    db.add(admin)
    db.commit()
    print("Admin created:", email, password)
else:
    print("Admin already exists")

db.close()
