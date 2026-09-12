from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import sqlite3
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect("lettro.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT,
            analysis TEXT,
            target_language TEXT,
            timestamp DATETIME
        )
    """)
    conn.commit()
    conn.close()

init_db()

class AnalysisRequest(BaseModel):
    text: str
    target_language: str = "en"
    analysis: Optional[str] = None

@app.post("/ocr")
async def ocr(image: UploadFile = File(...)):
    try:
        # Replace with actual OCR API call (e.g., Google Cloud Vision or Tesseract.js)
        return {"text": "Placeholder: Extracted text from OCR"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    try:
        text = request.text
        target_language = request.target_language

        # Replace with actual AI API call (e.g., Mistral AI or OpenAI)
        analysis = {
            "detected_language": "en",
            "sender": "Example Authority",
            "letter_type": "tax notice",
            "requires_action": True,
            "summary": "You must pay a tax underpayment of €200.",
            "deadline": {
                "date": "2026-10-15",
                "raw_text": "within 14 days of receipt",
                "is_relative_to_receipt": False,
                "confidence": "high"
            },
            "required_actions": [
                {"action": "Pay €200 by October 15, 2026", "confidence": "high"}
            ],
            "consequences_if_missed": "Late fees may apply.",
            "overall_confidence": "high"
        }
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_scan")
async def save_scan(request: AnalysisRequest):
    try:
        conn = sqlite3.connect("lettro.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scans (original_text, analysis, target_language, timestamp)
            VALUES (?, ?, ?, ?)
        """, (request.text, request.analysis, request.target_language, datetime.now()))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history():
    try:
        conn = sqlite3.connect("lettro.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scans ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()

        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "original_text": row[1],
                "analysis": row[2],
                "target_language": row[3],
                "timestamp": row[4]
            })
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
