"""
Orquestrador do pipeline completo do podcast de notícias de IA:
coleta (Fetch_news) -> filtro + roteiro via LLM (Generate_script) ->
áudio via TTS (Generate_audio).
"""

import sys

import Fetch_news
import Generate_script
import Generate_audio


def main():
    print("=== Etapa 1/3: coleta de notícias ===")
    Fetch_news.main()

    print("\n=== Etapa 2/3: filtro + roteiro (LLM) ===")
    Generate_script.main()

    print("\n=== Etapa 3/3: geração de áudio (TTS) ===")
    Generate_audio.main()

    print("\nPipeline concluído.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Pipeline falhou: {e}", file=sys.stderr)
        sys.exit(1)
