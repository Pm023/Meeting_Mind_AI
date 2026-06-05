from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize db instance here; will be bound in application factory
db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    meetings = db.relationship("Meeting", backref="author", lazy=True, cascade="all, delete-orphan")
    action_items = db.relationship("ActionItem", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Meeting(db.Model):
    __tablename__ = "meetings"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    filename = db.Column(db.String(300), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    
    # AI Output Fields
    transcript = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    
    # Store key discussion points and decisions as newline-separated strings or text
    key_points = db.Column(db.Text, nullable=True)
    decisions = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    action_items = db.relationship("ActionItem", backref="meeting", lazy=True, cascade="all, delete-orphan")

    def get_key_points_list(self):
        if not self.key_points:
            return []
        return [p.strip() for p in self.key_points.split("\n") if p.strip()]

    def get_decisions_list(self):
        if not self.decisions:
            return []
        return [d.strip() for d in self.decisions.split("\n") if d.strip()]

    def __repr__(self):
        return f"<Meeting {self.title}>"


class ActionItem(db.Model):
    __tablename__ = "action_items"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Foreign Keys
    meeting_id = db.Column(db.Integer, db.ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Task specific details
    assignee = db.Column(db.String(100), nullable=True)
    due_date = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<ActionItem {self.id} - Completed: {self.is_completed}>"
