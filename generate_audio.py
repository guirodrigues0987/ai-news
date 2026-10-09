"""
Step 3: Audio generation via TTS
Reads script.json (output of generate_script.py) and converts the "script"
field into a podcast file (mp3) using the ElevenLabs API.
"""

import json
import os
from datetime import UTC, datetime

from dotenv import load_dotenv
from elevenlabs import ElevenLabs, save
from elevenlabs.core import ApiError

load_dotenv()

# Default voice (multilingual, good quality). To change it, search voices
# (client.voices.search(language="pt")) and set ELEVENLABS_VOICE_ID in .env
# to the chosen voice_id.
DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
MODEL_ID = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"
OUTPUT_DIR = "output"


def load_script(path: str = "script.json") -> str:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["script"]


def generate_audio(script: str) -> str:
    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID") or DEFAULT_VOICE_ID

    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        text=script,
        model_id=MODEL_ID,
        output_format=OUTPUT_FORMAT,
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_DIR, f"podcast_{timestamp}.mp3")
    save(audio, output_path)

    print(f"Audio generated at: {output_path}")
    return output_path


def main() -> str:
    script = load_script()
    try:
        return generate_audio(script)
    except ApiError as e:
        print(f"Failed to generate audio with ElevenLabs: {e}")
        raise


if __name__ == "__main__":
    main()
