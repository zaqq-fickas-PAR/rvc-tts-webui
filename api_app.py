from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import argparse
import struct


from tts import tts


app = FastAPI()


class RvcOptions(BaseModel):
    rvc_model_name: str
    speed: int
    tts_text: str
    tts_voice: str
    f0_key_up: int
    f0_method: str
    index_rate: int
    protect0: float


@app.post("/tts")
def convert_text_to_rvc_speech(options: RvcOptions | None = None):
    def generate_audio_stream(sample_rate, audio_data):
        # Convert audio data to bytes
        audio_bytes = audio_data.tobytes()

        # Calculate the total length of audio data in bytes
        audio_length = len(audio_bytes)

        # Send the WAV header
        wav_header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            audio_length + 44,
            b"WAVE",
            b"fmt ",
            16,
            1,
            1,
            sample_rate,
            sample_rate * 2,
            2,
            16,
            b"data",
            audio_length,
        )
        yield wav_header

        # Send the audio data
        yield audio_bytes

    try:
        info_text, edge_tts_output, tts_output = tts(
            options.rvc_model_name,
            options.speed,
            options.tts_text,
            options.tts_voice,
            options.f0_key_up,
            options.f0_method,
            options.index_rate,
            options.protect0,
        )
        print(f"info_text: ${info_text}")
        print(f"edge_tts_output: ${edge_tts_output}")
        print(f"tts_output: ${tts_output}")
        return StreamingResponse(
            generate_audio_stream(tts_output[0], tts_output[1]), media_type="audio/wav"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "main":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    uvicorn.run(app, port=8001)
