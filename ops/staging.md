# Staging Environment

Docker Compose override for staging.

## docker-compose.staging.yml

```yaml
version: "3.8"

services:
  wikicapsule:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: wikicapsule-staging
    volumes:
      - wiki-staging-data:/wiki
      - ../config/config.staging.yaml:/wiki/.wikicapsule/config.yaml:ro
    environment:
      - WIKICAPSULE_WIKI_DIR=/wiki
      - WIKICAPSULE_TRANSPORT=sse
      - WIKICAPSULE_PORT=8080
      - WIKICAPSULE_LOG_LEVEL=DEBUG
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Optional: seed with test data
  seed:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    volumes:
      - wiki-staging-data:/wiki
      - ../sample-data:/seed-data:ro
    command: >
      bash -c "
        for f in /seed-data/*.md; do
          python -m wikicapsule.cli ingest \"$$f\" --type article;
        done
      "
    depends_on:
      - wikicapsule

volumes:
  wiki-staging-data:
    driver: local
```

## Usage

```bash
# Start staging
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.staging.yml up

# With seed data
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.staging.yml --profile seed up

# Tear down
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.staging.yml down -v
```

## Staging Config

`config/config.staging.yaml`:

```yaml
server:
  transport: sse
  port: 8080
  log_level: DEBUG

wiki:
  auto_commit: true
  lock_timeout_seconds: 30
  search:
    vector_model: "all-MiniLM-L6-v2"
    hybrid_alpha: 0.5

ingest:
  default_tags: ["staging"]
  extract_images: false
  summary_max_length: 1000

lint:
  orphan_threshold_days: 7
  stale_check_enabled: true
```

## Differences from Production

| Aspect | Production | Staging |
|--------|-----------|---------|
| Log level | INFO | DEBUG |
| Transport | stdio | SSE |
| Tags | None | staging |
| Image extract | true | false |
| Summary length | 2000 | 1000 |
| Orphan threshold | 30 days | 7 days |
| Data persistence | Permanent | Ephemeral (Docker volume) |
