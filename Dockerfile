FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements-app.txt .
RUN pip install -r requirements-app.txt

RUN useradd --system --create-home --uid 10001 app
COPY --chown=app:app app.py ./
COPY --chown=app:app data/owid-co2-data.csv data/ghg_features.csv data/scenario_projections.csv ./data/

USER app
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=40s \
  CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4).read() == b'ok' else 1)"

CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", \
     "--browser.gatherUsageStats=false", "--client.toolbarMode=viewer"]
