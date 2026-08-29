# Полностью воспроизводимый образ сканера (baseline-детекторы)
FROM python:3.11-slim

WORKDIR /app

# Зафиксированные зависимости — ключ к воспроизводимости
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Код и примеры
COPY scanner/ scanner/
COPY scripts/ scripts/
COPY examples/ examples/

# Точка входа: python -m scanner <аргументы>
ENTRYPOINT ["python", "-m", "scanner"]
CMD ["scan", "examples/example_repo"]