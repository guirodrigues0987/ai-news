# Project: AI News Podcast Agent

## Goal
Agent that fetches AI news (Hacker News + RSS from official blogs), filters it
by relevance, writes a podcast script with an LLM, converts the script to audio
with TTS and emails the episode - producing a podcast episode automatically.

## Context
- Portfolio project focused on LLM/GenAI engineering and Kubernetes deployment.
- The main PC cannot run Ollama, so external LLM APIs are used instead of a local model.
- Work is done directly on the target Lubuntu machine (hostname `homelab`), not over SSH.

## Stack
- Python, no agent framework - orchestration is implemented directly to understand the mechanics.
- LLM: Anthropic API, with Gemini as a fallback.
- TTS: ElevenLabs. Delivery: Gmail SMTP.
- Deployment: Docker image + k3s CronJob (`k8s/`).

## Pipeline
1. `fetch_news.py` - Hacker News API + RSS -> `news_raw.json`
2. `generate_script.py` - relevance filter, semantic dedup and script -> `script.json`
3. `generate_audio.py` - script -> mp3 in `output/`
4. `send_email.py` - mp3 as an email attachment
5. `main.py` - runs the four steps in order and exits non-zero on failure

## Deployment notes
- Namespace `ai-news`; CronJob `ai-news-podcast` runs daily at 06:00 (America/Sao_Paulo).
- Episodes are written to a `hostPath` volume (`/home/home_lab/ai-news/output`).
- Secrets live in the `ai-news-secrets` Secret, created from `.env`.
- The image is pulled from a private Docker Hub repository via `dockerhub-creds`.

## Conventions
- Conventional Commits in English (see `CONTRIBUTING.md`).
- Lint and format with Ruff before committing.
- Prefer small, concrete, testable steps over theory.
