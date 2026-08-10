FROM python:3.12-slim
WORKDIR /app
ENV PATCHPILOT_CONTAINER=1
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
RUN useradd --create-home --uid 10001 patchpilot
USER patchpilot
EXPOSE 8765
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/healthz')"
CMD ["patchpilot", "serve", "--host", "0.0.0.0", "--port", "8765"]
