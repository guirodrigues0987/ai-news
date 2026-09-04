# Imagem base leve — só o essencial do Python, sem peso extra
FROM python:3.12-slim

# Evita gerar arquivos .pyc e força output sem buffer (bom pra ver logs em tempo real no K3s)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copia só o requirements primeiro, pra aproveitar cache do Docker:
# se o código mudar mas as dependências não, essa camada não é reconstruída
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Agora copia o resto do código
COPY . .

# Pasta onde o podcast final vai ser salvo — no K3s isso vira um volume montado,
# assim o arquivo sobrevive depois que o container do CronJob termina
RUN mkdir -p /app/output

# Comando padrão: roda o pipeline completo (coleta -> roteiro -> áudio)
CMD ["python", "main.py"]
