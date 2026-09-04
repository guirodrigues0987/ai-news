"""
Passo 2: Filtro de relevância + geração de roteiro via LLM
Lê news_raw.json (saída do fetch_news.py), filtra os itens por relevância,
remove duplicatas semânticas e escreve um roteiro de podcast em tom de
apresentador — via API da Anthropic, com fallback para Gemini se a chamada
principal falhar.
"""

import json
import os
import sys

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-opus-4-8"

SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "selected_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "source": {"type": "string"},
                },
                "required": ["title", "url", "source"],
                "additionalProperties": False,
            },
        },
        "script": {"type": "string"},
    },
    "required": ["selected_items", "script"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """Você é o apresentador de um podcast diário sobre notícias de \
Inteligência Artificial. Você recebe uma lista de itens (Hacker News + RSS de \
blogs oficiais) e deve:

1. Selecionar apenas os itens realmente relevantes para quem acompanha IA de \
perto (pesquisadores, engenheiros, entusiastas) — descarte itens fracos, \
clickbait ou sem substância técnica/estratégica.
2. Remover duplicatas semânticas (itens diferentes cobrindo a mesma notícia), \
mantendo o de fonte mais confiável ou mais completa.
3. Escrever um roteiro de podcast em português, em tom de apresentador \
explicando as notícias com contexto e opinião leve — não é um resumo seco, \
é uma conversa envolvente, com abertura curta e fechamento.

Responda apenas com os dados estruturados pedidos."""


def load_news(path: str = "news_raw.json") -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_user_content(items: list[dict]) -> str:
    return f"Itens coletados:\n{json.dumps(items, ensure_ascii=False, indent=2)}"


def generate_script_anthropic(items: list[dict]) -> dict:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        output_config={
            "effort": "high",
            "format": {"type": "json_schema", "schema": SCRIPT_SCHEMA},
        },
        messages=[{"role": "user", "content": build_user_content(items)}],
    )
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


GEMINI_MODEL = "gemini-3.8-flash"


def generate_script_gemini(items: list[dict]) -> dict:
    """Fallback (não-Anthropic): Gemini, usado só se a chamada acima falhar."""
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    interaction = client.interactions.create(
        model=GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
        input=build_user_content(items),
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": SCRIPT_SCHEMA,
        },
    )
    return json.loads(interaction.output_text)


def main():
    items = load_news()
    try:
        result = generate_script_anthropic(items)
    except Exception as e:
        # Qualquer falha na Anthropic (API, rede, credencial ausente/inválida)
        # cai pro Gemini — não só erros de API.
        print(f"Chamada à Anthropic falhou ({e}); usando Gemini como fallback.", file=sys.stderr)
        result = generate_script_gemini(items)

    output_path = "roteiro.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Roteiro gerado com {len(result['selected_items'])} itens selecionados.")
    print(f"Salvo em: {output_path}")


if __name__ == "__main__":
    main()
