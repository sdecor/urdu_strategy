FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Zurich

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends tzdata \
  && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
  && dpkg-reconfigure -f noninteractive tzdata \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt || true

COPY src ./src
COPY config ./config
COPY data ./data
COPY state ./state
COPY logs ./logs
COPY .env.example ./.env.example

ENV PYTHONPATH=/app/src

RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "-u", "src/urdu_exec_bot/app.py"]
