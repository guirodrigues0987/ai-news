# Projeto: Agente de podcast de notícias de IA

## Objetivo
Agente que busca notícias de IA (Hacker News + RSS de blogs oficiais),
filtra por relevância, gera um roteiro de podcast via LLM e converte
o roteiro em áudio via TTS — produzindo um episódio de podcast
automaticamente.

## Contexto do usuário
- Em transição de carreira pra ML Engineering / Platform Engineer for AI
- Projeto pensado como peça de portfólio pra Upwork (foco em LLM/GenAI e,
  com esse projeto, também Kubernetes)
- Decidiu não usar mais dados/domínio de telecom nos projetos de portfólio
- PC principal não roda Ollama — por isso o uso de APIs externas de LLM
  em vez de modelo local

## Stack
- Linguagem: Python (sem framework de agentes — implementação direta,
  pra entender o mecanismo de tool use/orquestração)
- Dependências atuais: requests, feedparser
- LLM: API da Anthropic (chave disponível) + Gemini free tier como
  alternativa/fallback
- TTS: ainda não escolhido (candidatos: ElevenLabs free tier, OpenAI TTS)
- Deploy: Docker (imagem do agente) + K3s rodando como CronJob agendado.
  IMPORTANTE: esta sessão do Claude Code já roda direto na máquina Lubuntu
  de destino (hostname "homelab") — não é acesso via SSH a partir de outro
  computador, é a própria máquina.

## Arquitetura (fluxo)
1. Coleta: Hacker News (API pública) + RSS de blogs oficiais (OpenAI,
   Anthropic, Google DeepMind) -> news_raw.json
2. Filtro + roteiro: LLM filtra por relevância, remove duplicatas
   semânticas e escreve um roteiro em tom de podcast (não é um resumo
   seco, é um "apresentador" explicando as notícias)
3. Áudio: roteiro passa por uma API de TTS -> arquivo de podcast final
4. Execução: tudo empacotado em uma imagem Docker, rodando como CronJob
   no K3s (dispara sozinho no horário configurado, sem processo ficando
   ligado o tempo todo)

## Status atual
- [x] fetch_news.py: coleta HN + RSS, filtra por keywords, deduplica por
  título normalizado, salva em news_raw.json (testado localmente —
  funciona, mas não pôde ser testado no ambiente de desenvolvimento por
  restrição de rede; deve funcionar normalmente numa máquina com internet
  livre)
- [x] Dockerfile (Python 3.12-slim, cache de camada pro requirements,
  CMD ainda aponta só pro fetch_news.py) e requirements.txt prontos
- [x] Generate_script.py: lê news_raw.json, usa a API da Anthropic
  (claude-opus-4-8, structured outputs) para filtrar por relevância,
  deduplicar semanticamente e gerar o roteiro do podcast; fallback para
  Gemini (google-generativeai) se a chamada à Anthropic falhar. Salva em
  roteiro.json. Ainda não testado contra a API real (sem chave configurada
  neste ambiente).
- [x] Generate_audio.py: lê roteiro.json e converte o campo "script" em
  mp3 via ElevenLabs (eleven_multilingual_v2), salvando em output/. Voz
  configurável via ELEVENLABS_VOICE_ID no .env (padrão: voz multilíngue
  genérica — trocar por uma testada em pt-BR). Chaves e imports validados
  contra o pacote real; conversão em si não testada (sem chave de API
  configurada neste ambiente).
- [x] main.py: orquestrador que roda Fetch_news -> Generate_script ->
  Generate_audio em sequência; Dockerfile atualizado pra rodar main.py
  (e corrigido um bug latente: CMD apontava pro nome errado do arquivo,
  "fetch_news.py" em vez de "Fetch_news.py")
- [x] Diagnóstico do ambiente (feito em 2026-09-04): Ubuntu 24.04.4 LTS
  (LXQt = Lubuntu), kernel 7.0.0-30-generic, 4 CPUs, 3.7GB RAM (bem
  apertado — desktop + k3s + VSCode server já usam boa parte), swap de
  512MB ativo, 450GB de disco (410GB livres). curl instalado. Docker NÃO
  instalado (nem podman/buildah/nerdctl). ufw presente mas sudo pede senha
  (não dá pra checar status sem interação).
- [x] K3s já estava instalado e rodando (v1.36.3+k3s1, 20 dias de uptime,
  node "homelab" Ready, containerd 2.3.2-k3s2). kubectl configurado pro
  usuário home_lab sem precisar de sudo (~/.kube/config). Não precisou
  instalar do zero.
- [x] Limpeza: removida a CronJob de teste "meu-cronjob" (rodava a cada
  minuto há 20 dias, só um echo/date com busybox) e seus pods. O Job
  avulso "meu-job" (já completo, não recorrente) foi deixado como está.
- [x] Namespace "ai-news" criado.
- [x] k8s/pvc.yaml: PVC "ai-news-output" (2Gi, storageclass local-path,
  a default do k3s) pra guardar os episódios — aplicado, fica "Pending"
  até o primeiro pod usar (normal, WaitForFirstConsumer).
- [x] k8s/cronjob.yaml: CronJob "ai-news-podcast" (schedule "0 6 * * *",
  timeZone America/Sao_Paulo, concurrencyPolicy Forbid,
  activeDeadlineSeconds 1800, limits de CPU/memória modestos por causa da
  RAM apertada) — aplicado com suspend: true. Referencia imagem
  "ai-news:latest" com imagePullPolicy IfNotPresent (não usamos registry,
  a imagem é importada direto no containerd do k3s) e um Secret
  "ai-news-secrets" (envFrom) que ainda não existe.
- [ ] Pendente (requer sudo/senha, o usuário roda no terminal dele):
  instalar Docker, buildar a imagem (`docker build -t ai-news:latest .`)
  e importar pro containerd do k3s
  (`docker save ai-news:latest | sudo k3s ctr images import -`)
- [ ] Pendente: preencher .env com as chaves reais, criar o Secret
  "ai-news-secrets" no namespace ai-news (`kubectl create secret generic
  ai-news-secrets --from-env-file=.env -n ai-news`) e tirar o CronJob do
  suspend (`kubectl patch cronjob ai-news-podcast -n ai-news -p
  '{"spec":{"suspend":false}}'`)

## Preferências de trabalho
- Prefere entender o mecanismo por trás das coisas (ex: tool use sem
  framework) antes de usar abstrações prontas
- Prefere ir por etapas concretas e testáveis em vez de teoria solta
