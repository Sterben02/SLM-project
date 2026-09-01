# ============================================================
# SLM Secret Scanner — полный образ с моделью (воспроизводимо)
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Системные зависимости (нужны для tokenizers, git для HF)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Отключаем телеметрию и кеширование
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    PIP_NO_CACHE_DIR=1

# ============================================================
# Слой 1: зависимости (кешируется, меняется редко)
# ============================================================
COPY requirements-docker-slm.txt .

# Сначала ставим CPU-версию torch (воспроизводимо на любом железе),
# затем остальные зависимости
RUN pip install --upgrade pip \
    && pip install --index-url https://download.pytorch.org/whl/cpu torch==2.7.0 \
    && pip install -r requirements-docker-slm.txt

# ============================================================
# Слой 2: код (меняется часто, поэтому после зависимостей)
# ============================================================
COPY scanner/ scanner/
COPY scripts/ scripts/
COPY examples/ examples/

# ============================================================
# Слой 3: модели (~3 ГБ, кешируется отдельно)
# ============================================================
COPY models_cache/qwen-base/ models_cache/qwen-base/
COPY models_cache/qwen-secret-scanner-lora/ models_cache/qwen-secret-scanner-lora/

# ============================================================
# Слой 4: папка для отчётов
# ============================================================
RUN mkdir -p /app/reports

# Точка входа
ENTRYPOINT ["python", "-m", "scanner"]
# По умолчанию: каскад (полный функционал)
CMD ["scan", "examples/example_repo", "--with-slm", "--format", "markdown", "--out", "reports/report_docker.md"]