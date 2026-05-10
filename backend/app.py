from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="Python Tutor Bot")

# ───────────────── CORS ─────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────── DB SAFE ─────────────────
try:
    from db import conn, cursor
    DB_ENABLED = True
except:
    DB_ENABLED = False
    conn = None
    cursor = None

# ───────────────── MODEL SAFE LOAD ─────────────────
tutor_instance = None

def load_model(use_lora=True):
    try:
        from model import get_model
        return get_model(use_lora=use_lora)
    except Exception as e:
        print("MODEL ERROR:", e)
        return None

# ───────────────── FRONTEND ─────────────────
BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend", "build")
INDEX_FILE = os.path.join(FRONTEND_DIR, "index.html")

if os.path.exists(FRONTEND_DIR):
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")),
        name="static"
    )

# ───────────────── MODELS ─────────────────
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[list[Message]] = []
    use_lora: Optional[bool] = True

# ───────────────── ROUTES ─────────────────

@app.get("/")
def home():
    if os.path.exists(INDEX_FILE):
        return FileResponse(INDEX_FILE)
    return {"status": "backend running", "message": "frontend not found"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: ChatRequest):
    global tutor_instance

    try:
        # load model only once
        if tutor_instance is None:
            tutor_instance = load_model(req.use_lora)

        # fallback if model not loaded
        if tutor_instance is None:
            return {
                "response": "Model not loaded. Please check server logs.",
                "history": []
            }

        # convert history safely
        history = [
            {"role": m.role, "content": m.content}
            for m in (req.history or [])
        ]

        # generate response
        try:
            response = tutor_instance.generate(req.message, history)
        except Exception as e:
            print("MODEL GENERATION ERROR:", e)
            response = "Error generating response."

        if not response:
            response = "Empty response."

        # DB safe save
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
            except Exception as e:
                print("DB ERROR:", e)
                conn.rollback()

        return {
            "response": response,
            "history": history + [
                {"role": "user", "content": req.message},
                {"role": "assistant", "content": response}
            ]
        }

    except Exception as e:
        print("CHAT ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
def history():
    if not DB_ENABLED:
        return []

    try:
        cursor.execute("SELECT role, content FROM messages ORDER BY created_at")
        rows = cursor.fetchall()
        return [{"role": r[0], "content": r[1]} for r in rows]

    except Exception as e:
        print("HISTORY ERROR:", e)
        return []
