from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=50, message="Username must be between 3 and 50 characters")
    ])
    email = StringField("Email Address", validators=[
        DataRequired(message="Email address is required"),
        Email(message="Please enter a valid email address"),
        Length(max=150)
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required"),
        Length(min=6, max=100, message="Password must be at least 6 characters long")
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo("password", message="Passwords must match")
    ])
    submit = SubmitField("Create Account")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("That username is already taken. Please choose another one.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError("That email address is already registered. Please login instead.")


class LoginForm(FlaskForm):
    email = StringField("Email Address", validators=[
        DataRequired(message="Email address is required"),
        Email(message="Please enter a valid email address")
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required")
    ])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class MeetingUploadForm(FlaskForm):
    title = StringField("Meeting Title", validators=[
        DataRequired(message="Please provide a meeting title"),
        Length(min=3, max=150, message="Title must be between 3 and 150 characters")
    ])
    description = TextAreaField("Description (Optional)", validators=[
        Optional(),
        Length(max=500, message="Description must be under 500 characters")
    ])
    file = FileField("Meeting File (Audio, Video, Document, Image)", validators=[
        FileRequired(message="Please select a meeting file to upload"),
        FileAllowed([
            "mp3", "wav", "m4a",        # Audio
            "mp4", "webm", "avi", "mov", # Video
            "pdf", "txt",                # Documents
            "jpg", "jpeg", "png"         # Images
        ], "Only allowed media and documents (.mp3, .wav, .m4a, .mp4, .webm, .avi, .mov, .pdf, .txt, .jpg, .jpeg, .png) are supported.")
    ])
    submit = SubmitField("Process Meeting with AI")
