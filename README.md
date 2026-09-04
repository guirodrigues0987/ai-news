# AI News Podcast Agent

An autonomous agent that turns the day's AI news into a podcast episode —
no agent framework, hand-rolled orchestration end to end. Built as a
portfolio project to demonstrate practical LLM/GenAI engineering and
Kubernetes-based deployment.

## What it does

1. **Collects** the latest AI-related stories from Hacker News and official
   engineering blogs (OpenAI, Anthropic, Google DeepMind) via RSS.
2. **Filters and drafts** a podcast script with an LLM (Claude): scores
   relevance, removes semantic duplicates (not just exact-title matches),
   and writes the script in a natural, presenter-style tone rather than a
   dry summary.
3. **Narrates** the script into an MP3 episode via text-to-speech.
4. **Runs on a schedule** as a Kubernetes CronJob — no long-running process,
   the container starts, produces an episode, and exits.

## Architecture

```
Fetch_news.py  ---->  Generate_script.py  ---->  Generate_audio.py
(HN + RSS)            (Claude, Gemini          (ElevenLabs TTS)
                        as fallback)
     |                       |                        |
 news_raw.json          roteiro.json          output/podcast_*.mp3
```

`main.py` orchestrates the three steps in sequence. Each step is also a
standalone script that reads/writes a JSON file, so any stage can be run
and inspected independently.

| Stage | Script | Notes |
|---|---|---|
| Collection | `Fetch_news.py` | Hacker News top stories (last 48h) + RSS feeds, keyword-filtered, deduplicated by normalized title |
| Filtering + script | `Generate_script.py` | Anthropic API (`claude-opus-4-8`), structured JSON output (relevance filtering, semantic dedup, script generation). Falls back to Gemini if the Anthropic call fails |
| Text-to-speech | `Generate_audio.py` | ElevenLabs (`eleven_multilingual_v2`), configurable voice via env var |
| Orchestration | `main.py` | Runs the pipeline end to end; exits non-zero on failure so the CronJob reports it |

## Stack

- **Language:** Python, no agent framework — tool orchestration is
  implemented directly to understand the underlying mechanics rather than
  delegate it to an abstraction.
- **LLM:** [Anthropic API](https://platform.claude.com) (Claude), with
  Gemini as a fallback provider.
- **TTS:** [ElevenLabs](https://elevenlabs.io).
- **Packaging:** Docker.
- **Deployment:** [k3s](https://k3s.io) (lightweight Kubernetes) — the
  agent runs as a scheduled `CronJob`, with a `PersistentVolumeClaim` for
  generated episodes and `Secret`s for API keys and registry credentials.

## Project layout

```
Fetch_news.py       # Step 1: news collection
Generate_script.py  # Step 2: relevance filter + script generation (LLM)
Generate_audio.py   # Step 3: text-to-speech
main.py             # Orchestrator
Dockerfile           # Container image definition
requirements.txt     # Python dependencies
k8s/
  namespace.yaml     # Dedicated "ai-news" namespace
  pvc.yaml           # PersistentVolumeClaim for generated episodes
  cronjob.yaml        # Scheduled CronJob (daily, America/Sao_Paulo)
```

## Running locally

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
python main.py
```

Required environment variables (see `.env`):

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API access (script generation) |
| `GEMINI_API_KEY` | Fallback LLM if the Anthropic call fails |
| `ELEVENLABS_API_KEY` | Text-to-speech |
| `ELEVENLABS_VOICE_ID` | Optional — overrides the default voice |

Each step can also be run individually (`python Fetch_news.py`,
`python Generate_script.py`, `python Generate_audio.py`), which is useful
for debugging a single stage without re-running the whole pipeline.

## Deployment

The image is built with Docker and published to a private Docker Hub
repository. On the cluster:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/pvc.yaml
kubectl create secret generic ai-news-secrets --from-env-file=.env -n ai-news
kubectl apply -f k8s/cronjob.yaml
```

The `CronJob` fires daily, mounts the `PersistentVolumeClaim` at
`/app/output` so generated episodes survive past the container's
lifetime, and reads API keys from the `ai-news-secrets` Secret rather than
baking them into the image (a `.dockerignore` keeps `.env` out of the
build context entirely).

## Status

- [x] News collection (Hacker News + RSS)
- [x] Relevance filtering + script generation via LLM
- [x] Text-to-speech
- [x] Pipeline orchestration
- [x] Containerization + k3s deployment manifests
- [ ] API keys provisioning (Secret creation pending on the live cluster)
