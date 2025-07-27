import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
API_KEY = os.getenv("DEEPGRAM_API_KEY")
app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["POST"], allow_headers=["*"])


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """Transcribe audio file using Deepgram API"""
    if audio.content_type not in ("audio/wav", "audio/x-wav"):
        raise HTTPException(400, "Only WAV supported")

    body = await audio.read()
    params = {"model": "nova-2-general", "language": "en", "punctuate": "true", "smart_format": "true"}
    headers = {"Authorization": f"Token {API_KEY}", "Content-Type": "audio/wav"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post("https://api.deepgram.com/v1/listen", params=params, headers=headers, content=body)

    if resp.status_code != 200:
        raise HTTPException(502, "Deepgram API error")

    data = resp.json()
    text = data["results"]["channels"][0]["alternatives"][0]["transcript"].strip()
    return {"transcript": text}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
