from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import current_user, login_required
from app.models import db, ActionItem

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")

@tasks_bp.route("", methods=["GET"])
@login_required
def list_tasks():
    # Filter parameter: 'all', 'completed', 'pending'
    status_filter = request.args.get("status", "pending")
    
    query = ActionItem.query.filter_by(user_id=current_user.id)
    
    if status_filter == "completed":
        query = query.filter_by(is_completed=True)
    elif status_filter == "pending":
        query = query.filter_by(is_completed=False)
        
    # Order by creation date descending
    action_items = query.order_by(ActionItem.created_at.desc()).all()
    
    return render_template(
        "main/action_items.html",
        action_items=action_items,
        current_filter=status_filter
    )


@tasks_bp.route("/<int:item_id>/toggle", methods=["POST"])
@login_required
def toggle(item_id):
    action = ActionItem.query.get_or_404(item_id)
    
    # Security: ensure user owns this action item
    if action.user_id != current_user.id:
        abort(403)
        
    action.is_completed = not action.is_completed
    if action.is_completed:
        action.completed_at = datetime.utcnow()
    else:
        action.completed_at = None
        
    try:
        db.session.commit()
        
        # Support AJAX requests
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({
                "success": True, 
                "is_completed": action.is_completed,
                "message": "Task status updated"
            })
            
        flash("Task updated successfully.", "success")
    except Exception as e:
        db.session.rollback()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"success": False, "message": str(e)}), 500
        flash("Failed to update task.", "danger")
        
    return redirect(request.referrer or url_for("tasks.list_tasks"))
