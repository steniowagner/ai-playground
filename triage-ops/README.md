# TriageOps

TriageOps is a LangGraph incident-triage application with a FastAPI backend and
a Next.js frontend. Docker Compose runs the complete application as two
containers on a private network; the frontend proxies browser requests to the
API, so no browser-facing CORS configuration is required.

## Run with Docker Compose

### 1. Configure the model

Create the backend environment file from the example:

```bash
cp agent/.env.example agent/.env
```

Set both values in `agent/.env`:

```text
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=your-anthropic-model
```

The environment file is loaded only at container runtime and is excluded from
the image build context.

### 2. Build and start the application

From the repository root:

```bash
docker compose up --build
```

Open:

- Web application: http://localhost:3000
- API documentation: http://localhost:8000/docs

The frontend waits for the API health check before starting. The API container
includes the local incident fixtures, telemetry, runbooks, and sample prompts.

To change the public URL used in social metadata, set it while building:

```bash
NEXT_PUBLIC_SITE_URL=https://triage.example.com docker compose up --build
```

If the default host ports are already in use, override them without changing
the container network:

```bash
FRONTEND_PORT=13000 API_PORT=18000 docker compose up --build
```

### 3. Stop the application

```bash
docker compose down
```

## Container architecture

- `api`: Python 3.13, `uv`, FastAPI, and the LangGraph application on port 8000.
- `frontend`: minimal Next.js standalone production server on port 3000.
- `TRIAGE_API_URL=http://api:8000`: connects the frontend's server-side proxy to
  the backend over the Compose network.

## Run locally without Docker

Start the backend:

```bash
cd agent
uv sync
uv run fastapi dev
```

In another terminal, start the frontend:

```bash
cd frontend
pnpm install
pnpm dev
```

The local frontend defaults to an API at `http://127.0.0.1:8000`.
