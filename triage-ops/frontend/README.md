# TriageOps frontend

Next.js client for the FastAPI application in
`../agent/src/triage_ops/client/http`.

## Run locally

Start the FastAPI server on port `8000`, then run:

```bash
pnpm install
pnpm dev
```

Open `http://localhost:3000`.

The browser talks to the Next.js server at `/api/triage/*`. The server proxies
those requests to `http://127.0.0.1:8000` by default, so no CORS configuration is
needed. To use another API address, copy `.env.example` to `.env.local` and set
`TRIAGE_API_URL`. Set `NEXT_PUBLIC_SITE_URL` to the trusted public origin when
the frontend is deployed so social-preview URLs are absolute.

## Run with Docker

The repository-level `docker-compose.yaml` builds this application as a Next.js
standalone production server and connects it to the FastAPI container. From the
repository root, run:

```bash
docker compose up --build
```

## API behavior

- A new backend thread is created when the page loads or the session is reset.
- Message and approval requests consume the backend's POST-based SSE streams.
- Sample questions are fetched from `/sample-questions/` and rendered as a list.
- Raw model-thinking chunks are intentionally not displayed; the interface shows
  a generic working state instead.
