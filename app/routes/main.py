from flask import Blueprint, redirect, url_for, render_template, request
from flask_login import current_user, login_required
from app.models import db, Meeting, ActionItem

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    q = request.args.get("q", "").strip()
    
    # Fetch user meetings and actions
    user_meetings_query = Meeting.query.filter_by(user_id=current_user.id)
    user_action_query = ActionItem.query.filter_by(user_id=current_user.id)
    
    if q:
        user_meetings_query = user_meetings_query.filter(
            db.or_(
                Meeting.title.like(f"%{q}%"),
                Meeting.description.like(f"%{q}%"),
                Meeting.transcript.like(f"%{q}%")
            )
        )
    
    total_meetings = user_meetings_query.count() if not q else Meeting.query.filter_by(user_id=current_user.id).count()
    total_actions = user_action_query.count()
    completed_actions = user_action_query.filter_by(is_completed=True).count()
    pending_actions = total_actions - completed_actions
    
    # Calculate completion rate
    completion_rate = 0
    if total_actions > 0:
        completion_rate = round((completed_actions / total_actions) * 100)
        
    # Get meetings
    if q:
        # If searching, show all matched meetings
        recent_meetings = user_meetings_query.order_by(Meeting.created_at.desc()).all()
    else:
        # Otherwise show last 5 meetings
        recent_meetings = user_meetings_query.order_by(Meeting.created_at.desc()).limit(5).all()
    
    # Get last 5 pending action items
    recent_pending_tasks = user_action_query.filter_by(is_completed=False)\
                                             .order_by(ActionItem.created_at.desc())\
                                             .limit(5).all()
                                             
    return render_template(
        "main/dashboard.html",
        total_meetings=total_meetings,
        total_actions=total_actions,
        completed_actions=completed_actions,
        pending_actions=pending_actions,
        completion_rate=completion_rate,
        recent_meetings=recent_meetings,
        recent_pending_tasks=recent_pending_tasks,
        q=q
    )
