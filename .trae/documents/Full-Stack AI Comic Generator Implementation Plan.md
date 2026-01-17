# Full-Stack AI Comic Generator Implementation Plan

This plan details the creation of a web-based AI comic generator using Vue 3 (Frontend) and FastAPI (Backend), separating concerns into a modular architecture.

## 1. Project Structure Setup
We will create a root directory containing two main folders: `backend` and `frontend`.

### Backend Structure (`backend/`)
- **Framework**: FastAPI
- **Database**: SQLite (via SQLModel/SQLAlchemy) for storing project data and configs.
- **Directory Layout**:
  - `app/`
    - `core/`: Configuration (env vars, DB settings).
    - `models/`: Database models (SQLModel).
    - `schemas/`: Pydantic models for request/response validation.
    - `cruds/`: Database CRUD operations.
    - `routers/`: API endpoints grouped by functionality.
    - `services/`: Business logic (AI generation, File management).
    - `utils/`: Helper functions.
  - `static/`: Serving generated images.
  - `main.py`: Application entry point.

### Frontend Structure (`frontend/`)
- **Framework**: Vue 3 + Vite
- **UI Library**: Element Plus (Dark Mode enabled for "Tech" style).
- **Directory Layout**:
  - `src/`
    - `api/`: Axios instances for backend communication.
    - `components/`: Reusable UI components (JSON Editor, Image Cards).
    - `views/`: Main pages (Config, Workspace).
    - `stores/`: Pinia state management.

## 2. Backend Implementation Steps

### Phase 1: Core & Configuration
1.  **Environment**: Setup `requirements.txt` (FastAPI, SQLModel, Uvicorn, Google GenAI, OpenAI, python-dotenv).
2.  **Models & Schemas**:
    -   `ModelConfig`: Store API keys, provider (Google/OpenAI/DeepSeek), model names.
    -   `Project`: Store comic project metadata (title, status).
    -   `ComicData`: Store the generated JSONs (Global Config, Characters, Storyboard).
3.  **CRUDs**: Implement basic Create/Read/Update/Delete operations for Configs and Projects.

### Phase 2: AI Services Integration
1.  **AI Provider Adapter**: Create a unified interface to handle different providers (Google, DeepSeek, ChatGPT, etc.).
2.  **Migration**: Refactor logic from `comic_generator.py` into `services/comic_service.py`.
    -   Implement `generate_storyboard` (Text generation).
    -   Implement `generate_character_image` (Image generation).
    -   Implement `generate_comic_panel` (Image generation with context).
3.  **Endpoints**:
    -   `POST /api/generate/json`: Generate initial JSONs from user input.
    -   `POST /api/generate/image`: Generate specific image (Character or Panel).
    -   `POST /api/project/{id}/export`: Package and zip output.

## 3. Frontend Implementation Steps

### Phase 1: UI Framework & Configuration
1.  **Setup**: Initialize Vue 3 project, install Element Plus, Axios, Pinia, Vue Router.
2.  **Theme**: Configure Element Plus for Dark Mode/Tech style.
3.  **Model Configuration Page**:
    -   Form to add/edit API keys and select models for Text and Image generation.

### Phase 2: Comic Workflow Page
1.  **Step 1: Concept & JSON**:
    -   Input field for story idea.
    -   "Generate" button.
    -   **JSON Editor**: Integrated code editor (e.g., Monaco Editor) to modify generated JSONs (Global Config, Characters, Storyboard).
2.  **Step 2: Character Studio**:
    -   Display list of characters from JSON.
    -   "Generate/Regenerate" button for each character.
    -   Support "Add Character" manually.
3.  **Step 3: Comic Board**:
    -   Display storyboard panels.
    -   "Generate/Regenerate" button for each panel (4-grid or single).
    -   Support modifying prompt per panel.
4.  **Step 4: Export**:
    -   Button to download the complete comic package.

## 4. Execution Strategy
1.  **Backend First**: I will build the FastAPI backend, ensuring the API is functional and can replicate the existing script's logic.
2.  **Frontend Second**: I will build the Vue frontend and connect it to the backend.
3.  **Verification**: I will test the full flow: Config -> Story Input -> Edit JSON -> Generate Images -> Export.

I will begin by setting up the backend structure and dependencies.
