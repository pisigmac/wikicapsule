# Tests — Strategy, Coverage, and How to Run

## Philosophy

Three-tier testing: unit tests for logic, integration tests for workflows, and end-to-end tests for the full system. All tests use temporary directories — no test pollution, no mocking of the filesystem.

## Test Structure

```
tests/
├── unit/              # Fast, isolated, no I/O
├── integration/       # Full workflows with temp dirs
└── e2e/               # Server lifecycle, performance
```

## Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=src/wikicapsule --cov-report=term-missing

# Specific tiers
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# Specific test
pytest tests/unit/test_models.py -v
pytest -k "test_ingest" -v

# Stop on first failure
pytest -x

# Parallel execution
pytest -n auto
```

## Unit Tests

### test_models.py

Tests Pydantic model validation: Frontmatter, IngestRequest, QueryRequest, SearchRequest, PageCreateRequest, WikiPage, WikiStats.

**Coverage**: All model classes, validation rules, default values.

### test_config.py

Tests configuration loading: defaults, YAML parsing, environment variable overrides, path derivation, round-trip serialization.

**Coverage**: Config classes, YAML load/save, env var overrides.

### test_markdown.py

Tests markdown parsing: frontmatter extraction, wikilink detection, page rendering, content previews.

**Coverage**: parse_page, extract_wikilinks, create_page_content, get_content_preview.

### test_git_manager.py

Tests git operations: repo initialization, lock acquire/release, lock contention, context manager, commits, status reporting.

**Coverage**: GitManager, LockError, DirtyWorkingTreeError.

## Integration Tests

### test_ingest_flow.py

Tests the full ingest workflow: source ingestion, wiki page creation, raw storage, index updating, git committing, search indexing.

**Key scenarios**:
- Ingest article with tags
- Ingest with git commit
- Index rebuilt after ingest
- Search returns ingested content
- Hybrid search ranking

## End-to-End Tests

### test_server_lifecycle.py

Tests the full server lifecycle: creation with populated data, performance budgets.

**Key scenarios**:
- Server creation with test data
- Search latency < 500ms
- Query latency < 2s

## Test Data

5 sample documents in `sample-data/`:
1. Technical paper (Attention Is All You Need)
2. Blog article (RAG in production)
3. Meeting transcript (Q2 roadmap review)
4. Book chapter (MCP protocol)
5. Personal research notes

## Coverage Targets

| Module | Target | Status |
|--------|--------|--------|
| models.py | 100% | Complete |
| config.py | 100% | Complete |
| markdown.py | 100% | Complete |
| git_manager.py | 90% | Complete |
| search.py | 85% | Good |
| wiki.py | 80% | Good |
| tools.py | 75% | Needs work |
| resources.py | 80% | Good |
| prompts.py | 90% | Complete |
| server.py | 70% | Needs work |

## CI Pipeline

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev]"
      - run: pytest --cov=src/wikicapsule --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Adding Tests

When adding a feature:
1. Add unit tests for new models/parsers
2. Add integration tests for workflow changes
3. Run the full suite before committing
4. Maintain or improve coverage

## Performance Benchmarks

| Operation | Budget | Test |
|-----------|--------|------|
| Search | <500ms | `test_search_latency` |
| Query | <2s | `test_query_latency` |
| Ingest | <5s | Manual benchmark |
