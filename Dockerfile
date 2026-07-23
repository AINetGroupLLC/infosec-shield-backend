FROM python:3.12.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --system --gid 10001 shield \
    && useradd --system --uid 10001 --gid shield --home-dir /app shield

WORKDIR /app

COPY --chown=shield:shield requirements.txt ./
RUN pip install --no-cache-dir --requirement requirements.txt

COPY --chown=shield:shield main.py ./

USER shield

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import json, urllib.request; assert json.load(urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT', '8000') + '/health', timeout=3))['status'] == 'ok'"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
