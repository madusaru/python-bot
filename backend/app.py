# app.py — FastAPI backend server

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from db import conn, cursor
import uvicorn
import os

from model import get_model

# Load model once
tutor_instance = None

app = FastAPI(title="Python Tutor Bot ")

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

print("FRONTEND PATH:", FRONTEND_DIR)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ─── Request / Response Models ───────────────────────────────────────────────

class Message(BaseModel):
    role: str   # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[list[Message]] = []
    use_lora: Optional[bool] = True

class ChatResponse(BaseModel):
    response: str
    history: list[Message]


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)

@app.get("/health")
def health():
    return {"status": "ok", "model": "PythonTutorBot"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    global tutor_instance

    try:
        if tutor_instance is None:
            tutor_instance = get_model(use_lora=req.use_lora)

        # Convert history
        history = []
        if req.history:
            for m in req.history:
                history.append({
                    "role": m.role,
                    "content": m.content
                })

        # Generate response
        response = tutor_instance.generate(req.message, history)

        if not response:
            response = "Model returned empty response."

        # Save to DB
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

        return ChatResponse(
            response=response,
            history=history
        )

    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def history():
    cursor.execute(
        "SELECT role, content FROM messages ORDER BY created_at"
    )
    rows = cursor.fetchall()

    return [
        {"role": r[0], "content": r[1]}
        for r in rows
    ]

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
