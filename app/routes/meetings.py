import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, send_from_directory, current_app, jsonify
from flask_login import current_user, login_required
from app.models import db, Meeting, ActionItem
from app.forms import MeetingUploadForm
from app.services.file_service import save_upload_file, delete_upload_file
from app.services.ai_service import analyze_meeting_audio, answer_meeting_question

meetings_bp = Blueprint("meetings", __name__, url_prefix="/meetings")

@meetings_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    form = MeetingUploadForm()
    if form.validate_on_submit():
        audio_file = form.file.data
        try:
            # Save the file locally using secure file service
            filename, file_path = save_upload_file(audio_file, form.title.data)
            
            # Analyze using Gemini AI / fallback mockup
            ai_data = analyze_meeting_audio(
                file_path=file_path, 
                title=form.title.data, 
                description=form.description.data
            )
            
            # Formulate Meeting model
            meeting = Meeting(
                title=form.title.data,
                description=form.description.data,
                filename=filename,
                file_path=file_path,
                transcript=ai_data.get("transcript"),
                summary=ai_data.get("summary"),
                key_points="\n".join(ai_data.get("key_points", [])),
                decisions="\n".join(ai_data.get("decisions", [])),
                user_id=current_user.id
            )
            
            db.session.add(meeting)
            
            # Formulate ActionItem models
            for item in ai_data.get("action_items", []):
                if isinstance(item, dict):
                    task_content = item.get("task", "")
                    assignee = item.get("assignee", "Unassigned")
                    due_date = item.get("due_date", "Unassigned")
                else:
                    task_content = str(item)
                    assignee = "Unassigned"
                    due_date = "Unassigned"
                
                action = ActionItem(
                    content=task_content,
                    assignee=assignee,
                    due_date=due_date,
                    meeting=meeting,
                    user_id=current_user.id,
                    is_completed=False
                )
                db.session.add(action)
                
            db.session.commit()
            
            flash(f"Meeting '{meeting.title}' was successfully uploaded and analyzed by MeetingMind AI!", "success")
            return redirect(url_for("meetings.detail", meeting_id=meeting.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while processing your meeting: {str(e)}", "danger")
            
    return render_template("meetings/upload.html", form=form)


@meetings_bp.route("/<int:meeting_id>", methods=["GET"])
@login_required
def detail(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    # Security check: Ensure user owns this meeting
    if meeting.user_id != current_user.id:
        abort(403)
        
    return render_template("meetings/detail.html", meeting=meeting)


@meetings_bp.route("/audio/<path:filename>", methods=["GET"])
@login_required
def serve_audio(filename):
    # Security check: Make sure user owns the meeting referencing this filename
    meeting = Meeting.query.filter_by(filename=filename, user_id=current_user.id).first_or_404()
    return send_from_directory(current_app.config["UPLOAD_DIR"], filename)


@meetings_bp.route("/<int:meeting_id>/chat", methods=["POST"])
@login_required
def chat(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    # Security check: Ensure user owns this meeting
    if meeting.user_id != current_user.id:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
        
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"success": False, "message": "No query provided"}), 400
        
    question = data["message"].strip()
    if not question:
        return jsonify({"success": False, "message": "Query cannot be empty"}), 400
        
    try:
        answer = answer_meeting_question(meeting, question)
        return jsonify({"success": True, "response": answer})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@meetings_bp.route("/<int:meeting_id>/export", methods=["GET"])
@login_required
def export(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    # Security check: Ensure user owns this meeting
    if meeting.user_id != current_user.id:
        abort(403)
        
    from werkzeug.utils import secure_filename
    from flask import Response
    
    # Compile markdown text
    md_lines = []
    md_lines.append(f"# Meeting Report: {meeting.title}")
    md_lines.append(f"**Date:** {meeting.created_at.strftime('%B %d, %Y')}")
    md_lines.append(f"**Description:** {meeting.description or 'No description provided.'}")
    md_lines.append("")
    md_lines.append("## Executive Summary")
    md_lines.append(meeting.summary or "No summary available.")
    md_lines.append("")
    
    md_lines.append("## Key Discussion Points")
    key_points = meeting.get_key_points_list()
    if key_points:
        for pt in key_points:
            md_lines.append(f"- {pt}")
    else:
        md_lines.append("*No discussion points recorded.*")
    md_lines.append("")
    
    md_lines.append("## Decisions Reached")
    decisions = meeting.get_decisions_list()
    if decisions:
        for dec in decisions:
            md_lines.append(f"- {dec}")
    else:
        md_lines.append("*No decisions recorded.*")
    md_lines.append("")
    
    md_lines.append("## Action Items")
    if meeting.action_items:
        for task in meeting.action_items:
            status = "[x]" if task.is_completed else "[ ]"
            assignee = task.assignee or "Unassigned"
            due_date = task.due_date or "Unassigned"
            md_lines.append(f"- {status} {task.content}")
            md_lines.append(f"  - **Assignee:** {assignee}")
            md_lines.append(f"  - **Due Date:** {due_date}")
    else:
        md_lines.append("*No action items recorded.*")
        
    markdown_text = "\n".join(md_lines)
    
    # Generate filename
    safe_title = secure_filename(meeting.title)
    if not safe_title:
        safe_title = f"meeting_{meeting.id}"
    filename = f"{safe_title}_report.md"
    
    response = Response(markdown_text, mimetype="text/markdown")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@meetings_bp.route("/<int:meeting_id>/delete", methods=["POST"])
@login_required
def delete(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    # Security check: Ensure user owns this meeting
    if meeting.user_id != current_user.id:
        abort(403)
        
    # Keep track of paths
    file_path = meeting.file_path
    meeting_title = meeting.title
    
    try:
        # Delete from database (action items delete cascadingly)
        db.session.delete(meeting)
        db.session.commit()
        
        # Delete local audio file
        delete_upload_file(file_path)
        
        flash(f"Meeting '{meeting_title}' was successfully deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Could not delete meeting: {str(e)}", "danger")
        
    return redirect(url_for("main.dashboard"))
