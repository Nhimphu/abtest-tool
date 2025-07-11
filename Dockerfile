# Builder stage
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y upx && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt pyinstaller
COPY src ./src
RUN pyinstaller --onefile -n abtest-tool src/ui/main.py \
    && upx -9 dist/abtest-tool

# Runtime stage
FROM debian:stable-slim
WORKDIR /app
COPY --from=builder /app/dist/abtest-tool /usr/local/bin/abtest-tool
ENTRYPOINT ["abtest-tool"]
