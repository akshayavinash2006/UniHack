# Unilog Product Data Enrichment & URL Intelligence Platform

A polished B2B hackathon MVP that takes messy industrial catalogue rows and intelligently discovers verified manufacturer URLs using web search and AI-driven semantic selection.

## Architecture

* **Backend**: FastAPI (Python) orchestrating DuckDuckGo search, Gemini URL selection, and heuristic fallback ranking.
* **Frontend**: React + Vite + Tailwind CSS with a premium dashboard aesthetic.
* **Processing**: Asynchronous batch background tasks with Server-Sent Events (SSE) for live UI updates.

## Setup Instructions

### 1. Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

If you have a Gemini API Key, copy `.env.example` to `.env` in the `backend` directory and add it:
```env
GEMINI_API_KEY=your_key_here
```

Start the backend server:
```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

Open a new terminal window:

```bash
cd frontend
npm install
npm run dev
```

The application will be available at http://localhost:5173

## Hackathon Demo Story

1. Open **Single Product Demo**
2. Input messy data (e.g., Frigidaire PDSH4816AF)
3. Hit "Find Manufacturer Source"
4. The system demonstrates the pipeline: Search -> AI/Heuristic Relevance -> Selection
5. Show the candidate cards and explain WHY the URL was chosen (confidence score + signals).
6. Open **Batch Enrichment**
7. Load the Demo Dataset
8. Process 10 items
9. Show the **Live Pipeline Progress** (this demonstrates asynchronous scale without blocking the browser).
10. Review the final dashboard with KPIs (Match Rate, AI Selections, Human Review queue).
