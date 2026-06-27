# Database Schema

WikiCapsule uses a single SQLite database (`.wikicapsule/search.db`) for search indexing and logging.

## ER Diagram

```
┌─────────────────┐       ┌──────────────────────┐
│     pages       │       │  page_embeddings     │
├─────────────────┤       ├──────────────────────┤
│ id (PK)         │◄──────│ page_id (PK, FK)     │
│ path (UNIQUE)   │       │ embedding (BLOB)     │
│ title           │       └──────────────────────┘
│ content         │
│ type            │       ┌──────────────────────┐
│ tags (JSON)     │       │       sources        │
│ sources (JSON)  │       ├──────────────────────┤
│ created_at      │       │ id (PK)              │
│ updated_at      │       │ path                 │
└─────────────────┘       │ title                │
           │              │ type                 │
           │              │ ingested_at          │
           │              └──────────────────────┘
           ▼
┌─────────────────────────────────┐
│          pages_fts              │
│     (FTS5 virtual table)        │
├─────────────────────────────────┤
│ path, title, content            │
│ (content='pages',               │
│  content_rowid='id')            │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│            log                  │
├─────────────────────────────────┤
│ id (PK, AUTOINCREMENT)          │
│ timestamp                       │
│ operation                       │
│ summary                         │
│ details (JSON)                  │
└─────────────────────────────────┘
```

## Tables

### pages

Stores indexed wiki pages. One row per page.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment |
| path | TEXT | UNIQUE, NOT NULL | Relative path in wiki/ |
| title | TEXT | NOT NULL | Page title |
| content | TEXT | NOT NULL | Full markdown content |
| type | TEXT | | Page type (entity/concept/source/comparison/exploration) |
| tags | TEXT | | JSON array of tags |
| sources | TEXT | | JSON array of source IDs |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update time |

### pages_fts

FTS5 virtual table for full-text search. Automatically synced with `pages` via triggers.

| Column | Description |
|--------|-------------|
| path | Page path (indexed) |
| title | Page title (indexed) |
| content | Page content (indexed) |

**Triggers**:
- `pages_ai` (AFTER INSERT): Adds new row to FTS
- `pages_ad` (AFTER DELETE): Removes row from FTS
- `pages_au` (AFTER UPDATE): Deletes old, inserts new

### page_embeddings

Vector embeddings for semantic search. 384-dim float32 arrays (all-MiniLM-L6-v2).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| page_id | INTEGER | PRIMARY KEY, FK → pages.id | Page reference |
| embedding | BLOB | NOT NULL | Serialized float32 array |

### sources

Tracks ingested source documents.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID or slug |
| path | TEXT | NOT NULL | Path in raw/ directory |
| title | TEXT | NOT NULL | Document title |
| type | TEXT | | Source type |
| ingested_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Ingest time |

### log

Operation log mirroring the markdown `log.md`.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Entry ID |
| timestamp | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Entry time |
| operation | TEXT | NOT NULL | Operation type |
| summary | TEXT | NOT NULL | Brief description |
| details | TEXT | | JSON blob with extra info |

## Schema Creation SQL

```sql
-- Pages table
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    type TEXT,
    tags TEXT,
    sources TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FTS5 virtual table
CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
    path, title, content,
    content='pages', content_rowid='id'
);

-- Sync triggers
CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
    INSERT INTO pages_fts(rowid, path, title, content)
    VALUES (new.id, new.path, new.title, new.content);
END;

CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN
    INSERT INTO pages_fts(pages_fts, rowid, path, title, content)
    VALUES ('delete', old.id, old.path, old.title, old.content);
END;

CREATE TRIGGER IF NOT EXISTS pages_au AFTER UPDATE ON pages BEGIN
    INSERT INTO pages_fts(pages_fts, rowid, path, title, content)
    VALUES ('delete', old.id, old.path, old.title, old.content);
    INSERT INTO pages_fts(rowid, path, title, content)
    VALUES (new.id, new.path, new.title, new.content);
END;

-- Embeddings
CREATE TABLE IF NOT EXISTS page_embeddings (
    page_id INTEGER PRIMARY KEY,
    embedding BLOB NOT NULL,
    FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE CASCADE
);

-- Sources
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    title TEXT NOT NULL,
    type TEXT,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log
CREATE TABLE IF NOT EXISTS log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operation TEXT NOT NULL,
    summary TEXT NOT NULL,
    details TEXT
);
```

## Index Size Estimates

| Pages | FTS5 Index | Embeddings | Total |
|-------|-----------|------------|-------|
| 100 | ~2 MB | ~0.5 MB | ~3 MB |
| 1,000 | ~15 MB | ~5 MB | ~25 MB |
| 10,000 | ~100 MB | ~50 MB | ~170 MB |

## Notes

- The database is auto-created on first run
- It can be safely deleted and will be rebuilt from markdown files on next startup
- WAL mode is recommended for better concurrent read performance
- The database file should be gitignored (it's in `.wikicapsule/` which is gitignored by default)
