# Deployment Guide

Three deployment modes: Docker (recommended), bare metal, and systemd service.

## Docker (Recommended)

### Quick Start

```bash
# Clone the repo
git clone https://github.com/pisigmac/wikicapsule.git
cd wikicapsule

# Build and run
docker-compose -f docker/docker-compose.yml up --build
```

### Volume Persistence

The Docker Compose setup uses a named volume `wiki-data` that persists across container restarts.

```yaml
volumes:
  - wiki-data:/wiki  # Persists wiki content
```

### Custom Config

Mount your config file:

```yaml
volumes:
  - wiki-data:/wiki
  - ./my-config.yaml:/wiki/.wikicapsule/config.yaml:ro
```

### SSE Mode

```yaml
services:
  wikicapsule:
    build: .
    ports:
      - "8080:8080"
    environment:
      - WIKICAPSULE_TRANSPORT=sse
    command: ["--transport", "sse", "--port", "8080"]
```

### Health Check

The container includes a health check:

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import os; os.path.exists('/wiki/.wikicapsule/config.yaml')"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Bare Metal

### Prerequisites

- Python 3.11+
- Git
- C++ compiler (for sentence-transformers dependencies)

### Installation

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install
pip install -e ".[dev]"

# Download embedding model (first run)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Running

```bash
# Initialize wiki
mkdir ~/wiki && cd ~/wiki
python -m wikicapsule.server --wiki-dir ~/wiki

# Or use the CLI entry point
wikicapsule init ~/wiki
wikicapsule --wiki-dir ~/wiki stats
```

## systemd Service

### Unit File

Create `/etc/systemd/system/wikicapsule.service`:

```ini
[Unit]
Description=WikiCapsule MCP Server
After=network.target

[Service]
Type=simple
User=wikicapsule
Group=wikicapsule
WorkingDirectory=/home/wikicapsule/wiki
Environment="WIKICAPSULE_WIKI_DIR=/home/wikicapsule/wiki"
Environment="WIKICAPSULE_LOG_LEVEL=INFO"
Environment="WIKICAPSULE_TRANSPORT=sse"
Environment="WIKICAPSULE_PORT=8080"
ExecStart=/home/wikicapsule/venv/bin/python -m wikicapsule.server --transport sse --port 8080
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Setup

```bash
# Create user
sudo useradd -r -m -s /bin/bash wikicapsule

# Install
sudo -u wikicapsule bash -c '
  python3.11 -m venv ~/venv
  ~/venv/bin/pip install git+https://github.com/pisigmac/wikicapsule.git
'

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable wikicapsule
sudo systemctl start wikicapsule

# Check status
sudo systemctl status wikicapsule
sudo journalctl -u wikicapsule -f
```

## Reverse Proxy (nginx)

For SSE mode behind nginx:

```nginx
location /mcp/ {
    proxy_pass http://localhost:8080;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_read_timeout 86400;
}
```

## Cloud Deployment

### fly.io

```dockerfile
# Dockerfile (at repo root)
FROM python:3.11-slim
# ... (same as docker/Dockerfile)
EXPOSE 8080
CMD ["--transport", "sse", "--port", "8080"]
```

```toml
# fly.toml
app = "wikicapsule"
[build]
[http_service]
  internal_port = 8080
  force_https = true
[mounts]
  source = "wiki_data"
  destination = "/wiki"
```

### Render

Use the Docker Compose file. Set environment variables in the Render dashboard.

### AWS/GCP/Azure

Use the Docker image with their container services. Mount persistent storage for `/wiki`.

## Backup Strategy

Since the wiki is git-backed:

```bash
# Local backup
cd ~/wiki && git bundle create ~/backups/wiki-$(date +%Y%m%d).bundle --all

# Remote backup
cd ~/wiki && git push origin main

# Automated (cron)
0 2 * * * cd ~/wiki && git bundle create ~/backups/wiki-$(date +%Y%m%d).bundle --all
```

The SQLite search index (`search.db`) can be regenerated from the markdown files, so it doesn't need to be backed up. But backing it up avoids re-indexing time on restore.

## Migration

To move a wiki to a new server:

1. Copy the wiki directory (or clone from git remote)
2. Install WikiCapsule on the new server
3. Point `--wiki-dir` at the copied directory
4. The search index will rebuild automatically on first access
