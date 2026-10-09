"""
Step 4: Episode email delivery
Sends the generated mp3 (generate_audio.py) as an attachment via Gmail SMTP.
"""

import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
OUTPUT_DIR = "output"


def latest_mp3(output_dir: str = OUTPUT_DIR) -> str:
    mp3s = [f for f in os.listdir(output_dir) if f.endswith(".mp3")]
    if not mp3s:
        raise FileNotFoundError(f"No .mp3 found in {output_dir}/")
    mp3s.sort(key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))
    return os.path.join(output_dir, mp3s[-1])


def send_podcast_email(audio_path: str) -> None:
    sender = os.environ["EMAIL_SENDER"]
    password = os.environ["EMAIL_APP_PASSWORD"]
    recipient = os.environ.get("EMAIL_RECIPIENT") or sender

    msg = EmailMessage()
    msg["Subject"] = "Your daily AI news podcast"
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content("Today's episode is attached. Enjoy!")

    with open(audio_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="audio",
            subtype="mpeg",
            filename=os.path.basename(audio_path),
        )

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)

    print(f"Email sent to {recipient} with {os.path.basename(audio_path)}")


def main(audio_path: str | None = None) -> None:
    if audio_path is None:
        audio_path = latest_mp3()
    send_podcast_email(audio_path)


if __name__ == "__main__":
    main()
