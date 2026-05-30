FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
COPY config.example.toml ./
RUN pip install --no-cache-dir .
# config.toml + .env should be mounted at runtime
CMD ["cex-signal-lab"]
