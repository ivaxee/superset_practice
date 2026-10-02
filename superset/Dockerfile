# Superset 6.0 + драйвер Postgres (в lean-образах драйверов нет — ставим явно)
FROM apache/superset:6.0.0
USER root
RUN uv pip install --python /app/.venv/bin/python psycopg2-binary \
    || pip install --no-cache-dir psycopg2-binary
USER superset
