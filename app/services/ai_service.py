import json
import logging
import os
import time
from flask import current_app

logger = logging.getLogger(__name__)

# Try importing the modern google.genai SDK
try:
    from google import genai
    NEW_GENAI_AVAILABLE = True
    logger.info("google-genai (new SDK) is available.")
except ImportError:
    NEW_GENAI_AVAILABLE = False

# Try importing the classic google.generativeai SDK
try:
    import google.generativeai as legacy_genai
    LEGACY_GENAI_AVAILABLE = True
    logger.info("google-generativeai (legacy SDK) is available.")
except ImportError:
    LEGACY_GENAI_AVAILABLE = False

GENAI_AVAILABLE = NEW_GENAI_AVAILABLE or LEGACY_GENAI_AVAILABLE


def analyze_meeting_audio(file_path, title, description=""):
    """
    Process meeting upload (can be audio, video, image, or document).
    If Gemini API Key is available, uses the configured Gemini model version
    to analyze the file and return structured insights (transcript, summary, points, decisions, actions).
    Otherwise, falls back to custom high-quality mockups.
    """
    api_key = current_app.config.get("GEMINI_API_KEY")
    if api_key:
        api_key = api_key.strip()
    model_name = current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash")
    
    if GENAI_AVAILABLE and api_key:
        try:
            response_text = ""
            
            # Formulate the prompt for Gemini. We instruct it to analyze the modalities appropriately.
            prompt = (
                "You are MeetingMind AI, an elite virtual meeting analyst. "
                "Analyze the provided file (which could be an audio recording, a video, a document, or image notes) and generate a structured JSON object. "
                "Your response must be a single JSON object with EXACTLY the following keys. "
                "Do not include any Markdown styling (such as ```json or ```) or other preamble. "
                "Only return the raw JSON object string.\n\n"
                "JSON Keys:\n"
                "1. \"transcript\": A comprehensive transcript (if audio/video), a detailed plain-text extraction and structural outline of the document contents (if PDF/TXT), or a detailed analysis and description of the slides/whiteboard image (if image).\n"
                "2. \"summary\": A professional executive summary outlining the main objectives, discussion flow, and key highlights of the meeting or document.\n"
                "3. \"key_points\": A list of strings, each containing a major discussion point, theme, or finding.\n"
                "4. \"decisions\": A list of strings, each representing a distinct agreement, consensus, decision reached, or important resolution.\n"
                "5. \"action_items\": A list of objects, each representing an action item with EXACTLY three keys: "
                "\"task\" (string, the clear content description of the task), "
                "\"assignee\" (string, the person responsible or \"Unassigned\" if not mentioned), and "
                "\"due_date\" (string, the timeframe/deadline or \"Unassigned\" if not mentioned).\n\n"
                f"Context: The title of this meeting is '{title}'. Description/Goal: '{description}'."
            )
            
            # Case 1: Using google.genai (new SDK)
            if NEW_GENAI_AVAILABLE:
                logger.info(f"Invoking google-genai client with model: {model_name}")
                client = genai.Client(api_key=api_key)
                
                logger.info(f"Uploading file {file_path} to Gemini files API...")
                uploaded_file = client.files.upload(file=file_path)
                
                # Wait for file processing if necessary
                for _ in range(10):
                    file_info = client.files.get(name=uploaded_file.name)
                    if file_info.state.name == "ACTIVE":
                        break
                    elif file_info.state.name == "FAILED":
                        raise Exception("Gemini File API processing failed")
                    logger.info("Waiting for file to process...")
                    time.sleep(2)
                    
                logger.info("Generating content...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=[uploaded_file, prompt]
                )
                response_text = response.text
                
                # Cleanup file
                try:
                    client.files.delete(name=uploaded_file.name)
                    logger.info("Uploaded file removed from Gemini API storage.")
                except Exception as e:
                    logger.warning(f"Could not delete uploaded file from Gemini storage: {e}")
            
            # Case 2: Using google.generativeai (classic SDK)
            elif LEGACY_GENAI_AVAILABLE:
                logger.info(f"Invoking google-generativeai client with model: {model_name}")
                legacy_genai.configure(api_key=api_key)
                
                logger.info(f"Uploading file {file_path} to Gemini files API...")
                uploaded_file = legacy_genai.upload_file(path=file_path)
                
                for _ in range(10):
                    file_info = legacy_genai.get_file(uploaded_file.name)
                    if file_info.state.name == "ACTIVE":
                        break
                    elif file_info.state.name == "FAILED":
                        raise Exception("Gemini File API processing failed")
                    logger.info("Waiting for file to process...")
                    time.sleep(2)
                    
                logger.info("Generating content...")
                model = legacy_genai.GenerativeModel(model_name)
                response = model.generate_content([uploaded_file, prompt])
                response_text = response.text
                
                # Cleanup file
                try:
                    legacy_genai.delete_file(uploaded_file.name)
                    logger.info("Uploaded file removed from Gemini API storage.")
                except Exception as e:
                    logger.warning(f"Could not delete uploaded file from Gemini storage: {e}")
            
            # Clean up the output string
            response_text = response_text.strip()
            if response_text.startswith("```"):
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                else:
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

            result = json.loads(response_text)
            
            # Ensure return dict has all keys
            required_keys = ["transcript", "summary", "key_points", "decisions", "action_items"]
            for key in required_keys:
                if key not in result:
                    result[key] = [] if key in ["key_points", "decisions", "action_items"] else ""
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}.")
            # Raise the exception directly so routes catch and display the live API error
            raise e
            
    else:
        logger.info("Gemini API key not configured or no SDK available. Using simulation mode.")
        return _generate_mock_analysis(title, description, file_path)


def answer_meeting_question(meeting, question):
    """
    Answer a question about a specific meeting based on its transcript and details.
    """
    api_key = current_app.config.get("GEMINI_API_KEY")
    if api_key:
        api_key = api_key.strip()
    model_name = current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash")
    
    if GENAI_AVAILABLE and api_key:
        try:
            prompt = (
                "You are MeetingMind AI, an elite virtual meeting assistant. "
                "Answer the user's question about the meeting details based strictly on the provided transcript and summary. "
                "Be concise, clear, and professional. If the information is not in the transcript, politely state that it wasn't discussed in the meeting.\n\n"
                f"Meeting Title: {meeting.title}\n"
                f"Meeting Description: {meeting.description or 'No objective provided'}\n"
                f"Meeting Summary:\n{meeting.summary}\n\n"
                f"Meeting Transcript:\n{meeting.transcript}\n\n"
                f"User Question: {question}\n\n"
                "Answer:"
            )
            
            # Case 1: Using google.genai (new SDK)
            if NEW_GENAI_AVAILABLE:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response.text
                
            # Case 2: Using google.generativeai (classic SDK)
            elif LEGACY_GENAI_AVAILABLE:
                legacy_genai.configure(api_key=api_key)
                model = legacy_genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
                
        except Exception as e:
            logger.error(f"Error in meeting chat: {e}")
            raise e
            
    # Mock fallback response
    time.sleep(1.0)
    question_lower = question.lower()
    if "budget" in question_lower or "money" in question_lower:
        return "Based on the meeting data, the team approved a budget of $5,000 for paid LinkedIn ads. Finance sign-off is pending."
    elif "action" in question_lower or "task" in question_lower:
        return "The pending tasks include: John delivering graphic assets by Friday, Emily scheduling posts by next Tuesday, and Sarah submitting the budget request."
    elif "decision" in question_lower or "agree" in question_lower:
        return "The major decisions made were: allocating $5,000 for paid LinkedIn ads, and shifting the campaign launch to next Wednesday to integrate design assets."
    elif "summary" in question_lower or "outline" in question_lower:
        return f"This meeting covers the objectives for '{meeting.title}'. The team reviewed timelines, aligned on core deliverables, and delegated tasks to clear roadblocks."
    else:
        return f"This is a simulated AI response. You asked: '{question}'. Add a valid Gemini API key to query your meeting recordings in real-time."


def _generate_mock_analysis(title, description, file_path):
    """
    Generates realistic templates based on file suffix and keywords.
    """
    ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ""
    title_lower = title.lower()
    
    # Simulate API latency
    time.sleep(1.5)
    
    # Check Modality
    is_image = ext in ["png", "jpg", "jpeg"]
    is_doc = ext in ["pdf", "txt"]
    is_video = ext in ["mp4", "webm", "avi", "mov"]
    
    if is_image:
        return {
            "transcript": (
                "[Whiteboard Capture Transcript]\n"
                "Header: 'Sprint 15 Core Goals'\n"
                "- Left Column (Roadmap blockers):\n"
                "  * OAuth endpoints key-vault integration is red (unassigned).\n"
                "  * Stripe webhooks retry mechanism needs refactoring.\n"
                "- Right Column (Deliverables):\n"
                "  * Mark: Deliver schema migrations by Wednesday.\n"
                "  * Alice: DevOps IAM KMS policy checks.\n"
                "  * Tina: Integrate Figma templates for meeting details view."
            ),
            "summary": (
                f"MeetingMind AI analyzed the uploaded snapshot ('{title}'). "
                "The board outlines major sprint engineering bottlenecks, focusing heavily on security integrations and migrations. "
                "Key responsibilities were assigned to Mark, Alice, and Tina."
            ),
            "key_points": [
                "Roadmap blockers identified around OAuth endpoints and Stripe webhooks.",
                "Planning priorities focused on schema migrations and database reliability.",
                "Figma visual templates integration slated for front-end development."
            ],
            "decisions": [
                "OAuth vault integration priority bumped to highest severity.",
                "Assigned Mark to oversee database migrations."
            ],
            "action_items": [
                {"task": "Deliver schema migrations", "assignee": "Mark", "due_date": "Wednesday"},
                {"task": "Verify DevOps IAM KMS policies", "assignee": "Alice", "due_date": "Today"},
                {"task": "Integrate dashboard templates", "assignee": "Tina", "due_date": "Unassigned"}
            ]
        }
        
    elif is_doc:
        return {
            "transcript": (
                "[Document Outline & Text Extraction]\n"
                "Title: Strategic Meeting Brief - Q3 Objectives\n"
                "Author: Clara (Lead UX)\n\n"
                "1. User Registration Drop-offs:\n"
                "Analysis of funnel metrics indicates a 40% user drop-off at Step 3 (Billing Details Collection).\n"
                "2. Proposed Solutions:\n"
                "Move billing setup to the end of the 14-day free trial. Make initial signup billing-free.\n"
                "3. Timeline:\n"
                "Develop mockups by Wednesday. Deploy schema updates by Friday."
            ),
            "summary": (
                f"MeetingMind AI processed the uploaded brief document ('{title}'). "
                "The brief focuses on funnel friction and details plans to transition to a friction-free onboarding "
                "flow by making credit-card registrations optional."
            ),
            "key_points": [
                "Funnel metrics analysis showing major onboarding drop-offs at Step 3.",
                "Objective to increase trial signups by deferring billing input requirements.",
                "Development effort estimation for updating database schema parameters."
            ],
            "decisions": [
                "Onboarding billing step will be made optional during initial signup.",
                "Free trial period set to 14 days without upfront credit card requirements."
            ],
            "action_items": [
                {"task": "Design mockups for updated onboarding flow (mobile/desktop)", "assignee": "Leo", "due_date": "Wednesday"},
                {"task": "Modify database schema and endpoints to support null billing statuses", "assignee": "Mark", "due_date": "Friday"},
                {"task": "Update product specification document with the new trial policy", "assignee": "Clara", "due_date": "Unassigned"}
            ]
        }
        
    elif is_video:
        return {
            "transcript": (
                "Emma (CEO) [00:15]: Good afternoon team. Today we are reviewing our video metrics.\n"
                "Tom (CS) [00:45]: We see customer success tickets regarding onboarding friction. Users want a video tutorial.\n"
                "Emma [01:20]: That makes sense. Let's make an interactive tutorial and post a poll on Slack to see what date we want to launch it.\n"
                "Tom [02:00]: I will compile customer CS reports by Friday so marketing can use the data to script the video."
            ),
            "summary": (
                f"MeetingMind AI analyzed the meeting video file ('{title}'). "
                "The group reviewed onboarding questions, agreeing to film video tutorials to address user friction points. "
                "Tom will submit customer reports to prepare for script outlines."
            ),
            "key_points": [
                "Discussion of customer support tickets highlighting onboarding bottlenecks.",
                "Proposal to create interactive video guides for complex dashboard settings."
            ],
            "decisions": [
                "Approved development of new tutorial video guides for onboarding.",
                "A Slack poll will determine campaign release timelines."
            ],
            "action_items": [
                {"task": "Compile customer onboarding complaints report", "assignee": "Tom", "due_date": "Friday"},
                {"task": "Set up the retreat scheduling poll on Slack", "assignee": "Emma", "due_date": "Today"}
            ]
        }
        
    else:
        # Default Audio behavior / fallback
        if any(k in title_lower for k in ["marketing", "sales", "brand", "campaign"]):
            return {
                "transcript": (
                    "Sarah (Marketing Lead): Thanks everyone for joining. Today we're reviewing our Q3 marketing launch plan. "
                    "Currently, our visual assets are running a bit behind schedule. \n"
                    "John (Graphic Designer): Yes, I apologize. The design reviews took longer than expected, but I can have the final mockups ready by Friday. \n"
                    "Sarah: That works. We need them because our social media manager, Emily, has to schedule the campaigns by next Tuesday. "
                    "Emily, are you fine with that? \n"
                    "Emily (Social Media Manager): Absolutely. Once John sends the assets, I will set up the Sprout Social queue. \n"
                    "Sarah: Perfect. Let's also align on the budget. We agreed to allocate $5,000 for paid LinkedIn ads. "
                    "Let's finalize this budget adjustment today so finance can sign off."
                ),
                "summary": (
                    "The marketing team convened to review deliverables and finalize schedules for the upcoming Q3 campaign. "
                    "The primary bottlenecks identified were visual assets delays, which are currently being addressed. "
                    "The paid advertisement budget allocation of $5,000 for LinkedIn ads was formally approved."
                ),
                "key_points": [
                    "Discussion of visual design asset delays for the Q3 marketing campaign.",
                    "Review of social media scheduling timeline and Sprout Social queue preparation.",
                    "Review of paid marketing channels, specifically targeting LinkedIn advertising."
                ],
                "decisions": [
                    "Approved allocation of $5,000 exclusively for LinkedIn paid acquisition.",
                    "Agreed to move campaign launch date from Monday to next Wednesday to allow asset integration."
                ],
                "action_items": [
                    {"task": "Deliver final graphic assets to the team", "assignee": "John", "due_date": "Friday afternoon"},
                    {"task": "Draft and schedule Sprout Social posts", "assignee": "Emily", "due_date": "Next Tuesday"},
                    {"task": "Submit the budget request form to Finance for official sign-off", "assignee": "Sarah", "due_date": "Today"}
                ]
            }
        else:
            return {
                "transcript": (
                    "Emma (CEO): Hello team. Thanks for joining the weekly company sync. Let's start with our quarterly progress. "
                    "We are hitting 90% of our sales goals, but customer retention is flat. \n"
                    "Tom (Customer Success): We are seeing tickets related to onboarding friction. Users are getting stuck. "
                    "I think we need a clearer onboarding email sequence. \n"
                    "Emma: That's a good suggestion, Tom. Let's task the marketing team with creating a welcome drip email campaign. "
                    "Tom, please write a summary of the common onboarding complaints and share it with marketing. \n"
                    "Tom: Will do. I'll get that compiled by Friday. \n"
                    "Emma: Perfect. Also, we need to schedule our annual team retreat. Let's create a Slack poll to pick the best date."
                ),
                "summary": (
                    "The weekly company sync focused on quarterly performance metrics, customer success challenges, "
                    "and scheduling company retreat timings. While sales targets are on track, customer onboarding retention requires active improvements."
                ),
                "key_points": [
                    "Quarterly sales progress review and target metrics analysis.",
                    "Customer satisfaction updates highlighting onboarding bottlenecks.",
                    "Discussion regarding scheduling and locations for the upcoming company retreat."
                ],
                "decisions": [
                    "A Slack poll will be used to decide on dates for the annual retreat.",
                    "Approved development of a new welcome email drip campaign for user onboarding."
                ],
                "action_items": [
                    {"task": "Compile customer onboarding complaints report", "assignee": "Tom", "due_date": "Friday"},
                    {"task": "Send report to Marketing once complete", "assignee": "Tom", "due_date": "Unassigned"},
                    {"task": "Set up the retreat scheduling poll on Slack", "assignee": "Emma", "due_date": "Today"}
                ]
            }
