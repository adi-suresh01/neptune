# Neptune Frontend Context

This frontend is a Next.js app with a client-side UI for notes, filesystem, and the knowledge graph. The backend is discovered locally and accessed through a small API wrapper.

## Key Files

- `app/layout.tsx`: Root layout and global styling entry point.
- `app/page.tsx`: Main screen layout, backend health gating, and view toggles (graph vs notes).
- `app/globals.css`: Global styles.
- `lib/api.ts`: Backend discovery and all HTTP endpoints (filesystem, graph, search, embeddings).
- `components/FileSystemDisplay.js`: Fetches filesystem items and renders the left navigation tree.
- `components/NotesDisplay.js`: Note viewer/editor with optimistic checksum support.
- `components/KnowledgeGraph.js`: 3D graph visualization, graph refresh, and related note hover popups.
- `components/ui/*`: UI primitives used by the main screens.

## Data Flow

- Backend discovery runs once per session and retries as needed (`lib/api.ts`).
- Filesystem items are fetched on sidebar mount (`FileSystemDisplay.js`).
- Note content is fetched when a file is selected (`NotesDisplay.js`).
- Note updates send `content` and `content_checksum` to ensure the backend can detect conflicts.
- Knowledge graph data is fetched on load and can be refreshed on demand (`KnowledgeGraph.js`).
- Related notes for hover are retrieved from `/api/embeddings/related/{file_id}` and shown in the popup.

## Backend Endpoints Used

- Filesystem:
  - `GET /api/filesystem/`
  - `POST /api/filesystem/`
  - `GET /api/filesystem/{id}`
  - `PUT /api/filesystem/{id}/content`
  - `DELETE /api/filesystem/{id}`
  - `POST /api/filesystem/{id}/restore`
- Knowledge graph:
  - `GET /api/knowledge-graph/`
  - `POST /api/knowledge-graph/refresh`
  - `GET /api/knowledge-graph/status`
- Embeddings:
  - `POST /api/embeddings/backfill`
  - `GET /api/embeddings/related/{file_id}`
- Search:
  - `GET /api/search?q=...`

## Notes

- The UI is designed to run in desktop mode (Tauri) and local dev; backend discovery checks common ports.
- The knowledge graph nodes represent topics, not individual notes. Related notes are retrieved via embeddings on hover.
