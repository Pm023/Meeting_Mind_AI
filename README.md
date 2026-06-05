# ⚡ MeetingMind AI

> **Transform raw meeting recordings, videos, images, and documents into structured intelligence instantly.**

MeetingMind AI is an elite virtual meeting analyst and assistant. It parses uploaded files of multiple modalities to extract rich, actionable intelligence—including comprehensive transcripts, professional executive summaries, key discussion points, core decisions, and structured action items with assignees and due dates. It also includes an interactive Q&A assistant to query your meeting recordings in real-time.

---

## 🌟 Core Features

- 🎙️ **Multi-Modal Uploads**: Full support for **Audio** (`.mp3`, `.wav`, `.m4a`), **Video** (`.mp4`, `.webm`, `.avi`, `.mov`), **Documents** (`.pdf`, `.txt`), and **Images** (`.jpg`, `.jpeg`, `.png`).
- 👤 **AI-Extracted Task Details**: Automatically extracts task content, assigns task owners, and determines due dates/deadlines for action items.
- 🔍 **Interactive Keyword Search**: Filter meetings by title, description, or transcript content directly from your dashboard.
- 📑 **Markdown Report Export**: Download beautifully formatted meeting summaries, decisions, and checklists with a single click.
- 💬 **AI Q&A Chat Assistant**: Chat with your meeting files! Ask questions about budget allocations, specific follow-ups, or action items.
- 🎨 **Obsidian & Gold Aesthetics**: Premium, dark-mode design system with radial copper-warm glows and a structural blueprint canvas grid.

---

## 🛠️ Technology Stack

- **Core**: Python 3.13 / Flask
- **Database**: SQLite (SQLAlchemy ORM)
- **AI Engine**: Google Gemini API (`google-genai` & `google-generativeai` support)
- **Styling**: Vanilla CSS (readability optimized) + Bootstrap 5 + FontAwesome Icons
- **Auth**: Flask-Login + Secure Password Hashing

---

## 📂 Project Structure

```text
├── app/
│   ├── __init__.py           # Flask app factory with DB auto-migration engine
│   ├── models.py             # User, Meeting, and ActionItem database schemas
│   ├── forms.py              # User authentication and upload validation rules
│   ├── routes/
│   │   ├── auth.py           # Register, Login, and Logout views
│   │   ├── main.py           # Dashboard rendering & search query pipeline
│   │   ├── meetings.py       # Exporters, detail layouts, and chatbot endpoints
│   │   └── tasks.py          # Action items AJAX toggle endpoint
│   ├── services/
│   │   ├── file_service.py   # Secure file naming and local uploads utility
│   │   └── ai_service.py     # Gemini client SDK wrappers and simulation fallbacks
│   ├── static/
│   │   └── css/
│   │       └── style.css     # Bespoke Obsidian & Gold stylesheet
│   └── templates/            # High-fidelity dashboard & auth interfaces
├── config.py                 # Application configuration values
├── run.py                    # Server launch entry point
├── verify_app.py             # Automated pipeline validation tests
└── requirements.txt          # Package dependencies lists
```

---

## 🚀 Getting Started (Local Setup)

### 1. Clone & Navigate
```bash
git clone https://github.com/Pm023/Meeting_Mind_AI.git
cd Meeting_Mind_AI
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
SECRET_KEY=generate-a-secure-random-string
GEMINI_API_KEY=your-google-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Server
```bash
python run.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser, register an account, and upload your first meeting!
