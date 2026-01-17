# AI Comic Generator

[English](./README.md) | [中文](./README_CN.md)

An open-source AI-powered manga creation tool that transforms text stories into fully illustrated comics using Google Gemini models. Features include automatic storyboard generation, character consistency checks, and a visual editor.

![Project Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Backend-FastAPI-blue)
![Vue](https://img.shields.io/badge/Frontend-Vue3-green)

## ✨ Core Features

*   **Project Management**: Supports multi-project management, with each project independently saving story, characters, and storyboard data.
*   **Intelligent Scriptwriting**: Input simple story ideas, and AI automatically expands the plot and breaks it down into professional comic storyboard scripts (JSON format).
*   **Character Workshop**:
    *   Automatically extracts characters from the story and generates detailed character settings (three views).
    *   **Character Consistency**: Automatically references character setting images as references (Image-to-Image) when drawing.
    *   **Merge & Deduplication**: Supports manual merging of duplicate generated characters (e.g., "Butler Ma" and "Old Ma").
*   **Storyboard Editor**:
    *   Visually edit prompts, characters, and actions for each panel.
    *   Supports single-panel redrawing and batch generation.
    *   **Context Awareness**: Automatically reads previous storyboard panels and character images when generating storyboards to maintain style and plot continuity.
*   **Style Control**:
    *   Global style configuration (e.g., "Cyberpunk", "Ink Style"), forcing AI to follow settings.
    *   Supports custom dialog box and border styles.
*   **Background Tasks**: Time-consuming batch drawing tasks run in the background, supporting real-time progress viewing.

## 🛠️ Tech Stack

### Backend
*   **Framework**: FastAPI
*   **Database**: SQLite + SQLModel
*   **AI Service**: Google Gemini (Currently only supports Google's latest models)
    *   **Text Model**: `gemini-3-flash-preview`
    *   **Image Model**: `gemini-3-pro-image-preview`
*   **Task Queue**: FastAPI BackgroundTasks

### Frontend
*   **Framework**: Vue 3 + Vite
*   **UI Library**: Element Plus
*   **State Management**: Pinia
*   **HTTP Client**: Axios
*   **Package Manager**: pnpm

## 🚀 Quick Start

### Prerequisites
*   Python 3.9+
*   Node.js 16+
*   pnpm
*   Google Cloud API Key (Requires Gemini API access)

### 1. Backend Configuration

Enter the `backend` directory:

```bash
cd backend
```

Create virtual environment and install dependencies:

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

Create `.env` file and fill in API Key:

```ini
# backend/.env
GOOGLE_API_KEY="your_google_api_key_here"
```

Initialize the database using Alembic:

```bash
# Initialize alembic (if not already initialized)
alembic init alembic

# Generate migration script
alembic revision --autogenerate -m "Initial migration"

# Apply migration to database
alembic upgrade head
```

Start backend service:

```bash
# Windows (using provided script)
..\start_backend.bat

# Or run manually
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Configuration

Enter the `frontend` directory:

```bash
cd frontend
```

Install dependencies:

```bash
pnpm install
```

Start frontend service:

```bash
# Windows (using provided script)
..\start_frontend.bat

# Or run manually
pnpm dev
```

Access in browser: `http://localhost:5173`

## 📖 User Guide

1.  **Create Project**: Click "New Project" on the homepage and enter the comic title and introduction.
2.  **Story & Configuration**:
    *   Enter your story outline.
    *   Set global styles (e.g., "Japanese Shonen"), aspect ratio, etc.
    *   Click "Generate Storyboard Config", and AI will generate the character list and storyboard script.
3.  **Character Workshop**:
    *   View AI-generated character settings.
    *   Click "Draw" to generate character portraits.
    *   If there are duplicate characters, use the "Merge Characters" function to clean them up.
4.  **Storyboard Editing**:
    *   Check the description of each panel in the storyboard list.
    *   Click "Generate Image" or "Generate All" to start drawing the comic.
    *   Click on an image to view it in large size and support downloading.

## 📁 Directory Structure

```
aImanhua/
├── backend/            # FastAPI Backend
│   ├── app/            # Application Code
│   ├── static/         # Generated images and temp files storage
│   └── ...
├── frontend/           # Vue3 Frontend
│   ├── src/            # Pages and Components
│   └── ...
└── ...
```

## 📝 License

MIT License
