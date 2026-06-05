import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from config import Config
from app.models import db, User

# Extensions setup
csrf = CSRFProtect()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # User loader callback for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.meetings import meetings_bp
    from app.routes.tasks import tasks_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(meetings_bp)
    app.register_blueprint(tasks_bp)

    # Create database tables and structure if they don't exist
    with app.app_context():
        # Ensure upload folder exists
        os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)
        db.create_all()
        
        # SQLite Migration: check if 'assignee' column exists in 'action_items', if not ALTER TABLE
        try:
            db.session.execute(db.text("SELECT assignee FROM action_items LIMIT 1"))
        except Exception:
            db.session.rollback()
            try:
                db.session.execute(db.text("ALTER TABLE action_items ADD COLUMN assignee VARCHAR(100)"))
                db.session.execute(db.text("ALTER TABLE action_items ADD COLUMN due_date VARCHAR(100)"))
                db.session.commit()
                app.logger.info("Migrated SQLite database: added assignee and due_date to action_items table.")
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Auto-migration failed: {e}")

    return app
