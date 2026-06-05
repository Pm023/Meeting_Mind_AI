import sys
import os

def run_checks():
    print("=== STARTING MEETINGMIND AI INTEGRITY CHECKS ===")
    
    # 1. Check Python version
    print(f"Python Version: {sys.version}")
    
    # 2. Check workspace structure
    required_files = [
        "config.py",
        "run.py",
        "app/__init__.py",
        "app/models.py",
        "app/forms.py",
        "app/services/file_service.py",
        "app/services/ai_service.py",
        "app/routes/auth.py",
        "app/routes/main.py",
        "app/routes/meetings.py",
        "app/routes/tasks.py",
        "app/static/css/style.css",
        "app/templates/base.html",
        "app/templates/auth/login.html",
        "app/templates/auth/register.html",
        "app/templates/main/dashboard.html",
        "app/templates/main/action_items.html",
        "app/templates/meetings/upload.html",
        "app/templates/meetings/detail.html"
    ]
    
    missing_files = []
    for f in required_files:
        path = os.path.join(os.path.dirname(__file__), f)
        if not os.path.exists(path):
            missing_files.append(f)
            print(f"[ERROR] Missing file: {f}")
        else:
            print(f"[OK] File found: {f}")
            
    if missing_files:
        print(f"\n[FAIL] Codebase has {len(missing_files)} missing file(s).")
        return False
    
    print("\n[OK] All core application files verified.")

    # 3. Test Flask Application Factory and Routes loading
    try:
        from app import create_app
        from app.models import db, User, Meeting, ActionItem
        
        # Instantiate test app
        app = create_app()
        app.config["TESTING"] = True
        # Use in-memory SQLite for testing to avoid touching developer DB
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        
        # Test routing and database schemas
        with app.app_context():
            db.create_all()
            print("[OK] Database in-memory creation succeeded.")
            
        client = app.test_client()
        
        # Verify landing redirects to login when unauthorized
        res_landing = client.get("/", follow_redirects=False)
        assert res_landing.status_code == 302
        assert "/login" in res_landing.headers["Location"]
        print("[OK] Landing redirect verified (redirects to Login).")

        # Verify dashboard redirects to login when unauthorized
        res_dash = client.get("/dashboard", follow_redirects=False)
        assert res_dash.status_code == 302
        assert "/login" in res_dash.headers["Location"]
        print("[OK] Dashboard authentication wall verified (redirects to Login).")
        
        # Verify auth pages load (GET requests)
        res_login = client.get("/login")
        assert res_login.status_code == 200
        assert b"Sign In" in res_login.data
        print("[OK] Login view rendered successfully.")
        
        res_register = client.get("/register")
        assert res_register.status_code == 200
        assert b"Create Account" in res_register.data
        print("[OK] Registration view rendered successfully.")
        
    except Exception as e:
        print(f"\n[FAIL] Flask initialization or routing tests crashed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    print("\n=== SUCCESS: ALL MEETINGMIND AI INTEGRITY CHECKS PASSED ===")
    return True

if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
