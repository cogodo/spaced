import base64
import io
import wave

import numpy as np
import openai
import soundfile as sf
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from app.config import Settings, get_settings
from core.monitoring.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


# In a real application, you would use a proper TTS service.
# For this PoC, we will mock the TTS response.
def mock_tts(text: str) -> bytes:
    """Mocks a text-to-speech service by returning empty bytes."""
    # In a real implementation, this would call Google TTS, Polly, etc.
    # and return the audio bytes of the spoken text.
    return b""


@router.post("/transcribe-and-chat")
async def transcribe_and_chat(
    audio_file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
):
    """
    Receives an audio file, transcribes it, gets a chat response,
    and returns the audio of the response.
    """
    logger.info("Received request for /transcribe-and-chat")
    try:
        # Initialize client with API key from settings
        client = openai.OpenAI(api_key=settings.openai_api_key)

        # 1. Transcribe audio using OpenAI
        audio_bytes = await audio_file.read()
        logger.info(f"Received audio file '{audio_file.filename}' with size {len(audio_bytes)} bytes.")

        if not audio_bytes:
            logger.warning("Audio file is empty. OpenAI will likely reject this.")

        logger.info("Sending audio to OpenAI for transcription...")
        # The new API expects a file-like object with a name
        transcript_response = client.audio.transcriptions.create(
            model="whisper-1",
            file=(audio_file.filename, audio_bytes),
        )
        transcript = transcript_response.text
        logger.info(f"Successfully transcribed audio. Transcript: '{transcript}'")

        # 2. Get chat completion
        logger.info("Sending transcript to OpenAI for chat completion...")
        chat_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": transcript},
            ],
            stream=False,
        )
        chat_text = chat_response.choices[0].message.content
        logger.info(f"Successfully received chat completion: '{chat_text}'")

        # 3. Convert chat response to speech (mocked)
        logger.info("Performing mock TTS on chat response...")
        tts_audio_bytes = mock_tts(chat_text)
        tts_audio_base64 = base64.b64encode(tts_audio_bytes).decode("utf-8")
        logger.info("Successfully created response object.")

        return {
            "transcript": transcript,
            "chat": chat_text,
            "tts_audio_base64": tts_audio_base64,
        }
    except openai.APIStatusError as e:
        logger.error(
            f"OpenAI API error in /transcribe-and-chat: {e.status_code} - {e.response}",
            exc_info=True,
        )
        raise HTTPException(status_code=e.status_code, detail=str(e.response))
    except Exception as e:
        logger.error(f"An error occurred in /transcribe-and-chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Define audio format constants
INCOMING_SAMPLE_RATE = 48000  # Browsers typically send audio at 48kHz
TARGET_SAMPLE_RATE = 16000  # Whisper expects 16kHz
BITS_PER_SAMPLE = 16
CHANNELS = 1
BYTES_PER_SECOND = INCOMING_SAMPLE_RATE * (BITS_PER_SAMPLE // 8) * CHANNELS
BUFFER_SECONDS = 3
BUFFER_SIZE = BYTES_PER_SECOND * BUFFER_SECONDS


def _log_transcript(transcript: str):
    """Synchronously logs the transcript to a file."""
    try:
        with open("whisper_transcripts.log", "a") as log_file:
            log_file.write(f"{transcript}\n")
    except Exception as e:
        logger.error(f"Failed to write to transcript log file: {e}")


def _resample_and_transcribe(pcm_buffer: bytearray, client: openai.OpenAI) -> str:
    """
    Synchronously resamples audio and sends it to OpenAI for transcription.
    This is designed to be run in a thread pool.
    """
    # Save the original buffer to a WAV file for inspection
    try:
        with wave.open("debug_audio_chunk_48kHz.wav", "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(BITS_PER_SAMPLE // 8)
            wf.setframerate(INCOMING_SAMPLE_RATE)
            wf.writeframes(bytes(pcm_buffer))
        logger.info("Saved original audio chunk to debug_audio_chunk_48kHz.wav")
    except Exception as e:
        logger.error(f"Failed to save debug audio file: {e}")

    audio_np = np.frombuffer(bytes(pcm_buffer), dtype=np.int16)
    num_samples = len(audio_np)
    resampled_audio = np.interp(
        np.linspace(0, num_samples, int(num_samples * TARGET_SAMPLE_RATE / INCOMING_SAMPLE_RATE)),
        np.arange(num_samples),
        audio_np,
    ).astype(np.int16)

    wav_buffer = io.BytesIO()
    with sf.SoundFile(
        wav_buffer, "w", samplerate=TARGET_SAMPLE_RATE, channels=CHANNELS, subtype="PCM_16", format="WAV"
    ) as f:
        f.write(resampled_audio)
    wav_buffer.seek(0)

    # Save the resampled buffer for comparison
    try:
        with wave.open("debug_audio_chunk_16kHz.wav", "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(BITS_PER_SAMPLE // 8)
            wf.setframerate(TARGET_SAMPLE_RATE)
            wf.writeframes(wav_buffer.getvalue())
        logger.info("Saved resampled audio chunk to debug_audio_chunk_16kHz.wav")
    except Exception as e:
        logger.error(f"Failed to save resampled debug audio file: {e}")
    wav_buffer.seek(0)

    transcript_response = client.audio.transcriptions.create(
        model="whisper-1",
        file=("resampled_audio.wav", wav_buffer.read()),
    )
    return transcript_response.text


@router.websocket("/ws/voice")
async def ws_voice(websocket: WebSocket, settings: Settings = Depends(get_settings)):
    """
    Handles streaming voice, resamples it, and sends it for transcription.
    """
    await websocket.accept()
    logger.info("WebSocket connection established. Ready for 48kHz audio data.")

    pcm_buffer = bytearray()
    client = openai.OpenAI(api_key=settings.openai_api_key)

    try:
        while True:
            data = await websocket.receive_bytes()
            pcm_buffer.extend(data)

            if len(pcm_buffer) >= BUFFER_SIZE:
                logger.info(f"Buffer full ({len(pcm_buffer)} bytes). Offloading for transcription.")

                transcript = await run_in_threadpool(_resample_and_transcribe, pcm_buffer, client)
                logger.info(f"Transcript received: '{transcript}'")

                await run_in_threadpool(_log_transcript, transcript)

                # Send transcript to client, AI chat logic is now handled by client
                await websocket.send_json({"type": "transcript", "text": transcript})

                pcm_buffer.clear()

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed by client.")
    except Exception as e:
        logger.error(f"An error occurred in the WebSocket: {e}", exc_info=True)
    finally:
        logger.info("WebSocket connection closed.")
