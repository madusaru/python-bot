# app.py — FastAPI backend server

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os

app = FastAPI(title="Python Tutor Bot")

# ─── CORS ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── OPTIONAL DB (SAFE IMPORT) ────────────────────────
try:
    from db import conn, cursor
    DB_ENABLED = True
except Exception as e:
    print("DB DISABLED:", e)
    DB_ENABLED = False

# ─── MODEL (LAZY LOAD SAFE) ───────────────────────────
tutor_instance = None

def load_model(use_lora=True):
    try:
        from model import get_model
        return get_model(use_lora=use_lora)
    except Exception as e:
        print("MODEL LOAD ERROR:", e)
        return None

# ─── FRONTEND (SAFE PATH) ─────────────────────────────
BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend", "build")

index_path = os.path.join(FRONTEND_DIR, "index.html")

if os.path.exists(FRONTEND_DIR):
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")),
        name="static"
    )

# ─── MODELS ───────────────────────────────────────────
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[list[Message]] = []
    use_lora: Optional[bool] = True

class ChatResponse(BaseModel):
    response: str
    history: list[Message]

# ─── ROUTES ───────────────────────────────────────────

@app.get("/")
def serve_frontend():
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Backend is running"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "db": DB_ENABLED
    }

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    global tutor_instance

    try:
        if tutor_instance is None:
            tutor_instance = load_model(req.use_lora)

        if tutor_instance is None:
            return ChatResponse(
                response="Model not loaded properly.",
                history=[]
            )

        # Convert history
        history = []
        for m in req.history or []:
            history.append({"role": m.role, "content": m.content})

        # Generate response
        response = tutor_instance.generate(req.message, history)

        if not response:
            response = "Empty response from model."

        # Save to DB safely
        if DB_ENABLED:
            try:
                cursor.execute(
                    "INSERT INTO messages (session_id, role, content) VALUES (%s, %s, %s)",
                    ("user1", "user", req.message)
                )

                cursor.execute(
                    "INSERT INTO messages (session_id, role, content) VALUES (%s, %s, %s)",
                    ("user1", "assistant", response)
                )

                conn.commit()

            except Exception as db_error:
                print("DB ERROR:", db_error)
                conn.rollback()

        history.append({"role": "user", "content": req.message})
        history.append({"role": "assistant", "content": response})

        return ChatResponse(response=response, history=history)

    except Exception as e:
        print("CHAT ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def history():
    if not DB_ENABLED:
        return []

    try:
        cursor.execute(
            "SELECT role, content FROM messages ORDER BY created_at"
        )
        rows = cursor.fetchall()

        return [{"role": r[0], "content": r[1]} for r in rows]

    except Exception as e:
        print("HISTORY ERROR:", e)
        return []

# ─── LOCAL RUN ────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
