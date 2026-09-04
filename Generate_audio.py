"""
Passo 3: Geração de áudio via TTS
Lê roteiro.json (saída do Generate_script.py) e converte o campo "script"
em um arquivo de podcast (mp3) usando a API da ElevenLabs.
"""

import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from elevenlabs import ElevenLabs, save
from elevenlabs.core import ApiError

load_dotenv()

# Voz padrão (multilíngue, boa qualidade). Para trocar, rode uma busca de
# vozes (client.voices.search(language="pt")) e defina ELEVENLABS_VOICE_ID
# no .env com o voice_id escolhido.
DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
MODEL_ID = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"
OUTPUT_DIR = "output"


def load_script(path: str = "roteiro.json") -> str:
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
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_DIR, f"podcast_{timestamp}.mp3")
    save(audio, output_path)

    print(f"Áudio gerado em: {output_path}")
    return output_path


def main() -> str:
    script = load_script()
    try:
        return generate_audio(script)
    except ApiError as e:
        print(f"Falha ao gerar áudio na ElevenLabs: {e}")
        raise


if __name__ == "__main__":
    main()
