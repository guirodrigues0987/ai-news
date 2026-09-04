"""
Orquestrador do pipeline completo do podcast de notícias de IA:
coleta (Fetch_news) -> filtro + roteiro via LLM (Generate_script) ->
áudio via TTS (Generate_audio) -> envio por e-mail (Send_email).
"""

import sys

import Fetch_news
import Generate_script
import Generate_audio
import Send_email


def main():
    print("=== Etapa 1/4: coleta de notícias ===")
    Fetch_news.main()

    print("\n=== Etapa 2/4: filtro + roteiro (LLM) ===")
    Generate_script.main()

    print("\n=== Etapa 3/4: geração de áudio (TTS) ===")
    audio_path = Generate_audio.main()

    print("\n=== Etapa 4/4: envio por e-mail ===")
    Send_email.main(audio_path)

    print("\nPipeline concluído.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Pipeline falhou: {e}", file=sys.stderr)
        sys.exit(1)
