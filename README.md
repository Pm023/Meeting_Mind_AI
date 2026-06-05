# MeetingMind AI

MeetingMind AI is an elite virtual meeting analyst and assistant. It processes files in multiple modalities (audio, video, documents, and whiteboard snapshots) to generate transcripts, summaries, decisions, and action items with assignee and due date tags. It also includes an interactive AI Chatbot to ask questions directly about your meetings.

Designed with a premium **Nordic Obsidian & Champagne Gold** styling system, it feels sleek, responsive, and professional.

---

## Key Features

1. **Multi-Modal Uploads**:
   - Accepts **Audio** (`.mp3`, `.wav`, `.m4a`), **Video** (`.mp4`, `.webm`, `.avi`, `.mov`), **Documents** (`.pdf`, `.txt`), and **Images** (`.jpg`, `.jpeg`, `.png`).
   - Adapts the UI media player layout to match the uploaded format (HTML5 player, slide frames, or document download links).

2. **AI-Extracted Task Details**:
   - Captures owner/assignee names (e.g., "Emily") and timelines/due dates (e.g., "Next Tuesday") for every action item.
   - Highlights task information with colored gold and primary status badges.

3. **Dashboard Interactive Search**:
   - Premium magnifying-glass search input that instantly filters meetings by title, description, or transcript keywords.

4. **Markdown Report Export**:
   - "Export Report" download utility generating highly readable `.md` files containing the meeting title, date, executive summaries, decisions, and checklist status.

5. **Meeting Q&A Chatbot**:
   - Tabbed workspace details featuring an assistant interface where you can chat about the meeting transcript using suggestion chips or typing questions.

6. **Flexible API Configurations**:
   - Dual support for `google-genai` (new SDK) and `google-generativeai` (legacy SDK).
   - Swappable models via environment variables (`GEMINI_MODEL=gemini-2.5-flash`, etc.).

---

## Tech Stack & Architecture

- **Backend**: Flask (Python 3.13)
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: Vanilla CSS + Bootstrap 5 + FontAwesome Icons
- **AI Integration**: Google Gemini API (files upload & text models)
- **Authentication**: Flask-Login + Werkzeug Passwords
- **Deployment**: Vercel Serverless

---

## Getting Started (Local Setup)

### 1. Clone the repository:
```bash
git clone https://github.com/Pm023/Meeting_Mind_AI.git
cd Meeting_Mind_AI
```

### 2. Configure environment:
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-flask-secret-key
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
```

### 3. Run the application:
```bash
pip install -r requirements.txt
python run.py
```
Visit `http://127.0.0.1:5000` to register, log in, and try out the upload flow!

---

## Deployment on Vercel

MeetingMind AI is configured for serverless execution on Vercel using `vercel.json` and a serverless entry point `api/index.py`.

### 1. Install Vercel CLI:
```bash
npm install -g vercel
```

### 2. Run locally:
```bash
vercel dev
```

### 3. Deploy to Vercel:
```bash
vercel --prod
```

During initialization on serverless runtimes, SQLite files and file upload folders are automatically redirected to the writable `/tmp` directory. For production databases, configure the `DATABASE_URL` environment variable to point to a persistent PostgreSQL or MySQL instance.
