"""
End-to-end orchestrator for the AI news podcast pipeline:
collection (fetch_news) -> LLM filtering + script (generate_script) ->
TTS audio (generate_audio) -> email delivery (send_email).
"""

import sys

import fetch_news
import generate_audio
import generate_script
import send_email


def main():
    print("=== Step 1/4: news collection ===")
    fetch_news.main()

    print("\n=== Step 2/4: filtering + script (LLM) ===")
    generate_script.main()

    print("\n=== Step 3/4: audio generation (TTS) ===")
    audio_path = generate_audio.main()

    print("\n=== Step 4/4: email delivery ===")
    send_email.main(audio_path)

    print("\nPipeline finished.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)
