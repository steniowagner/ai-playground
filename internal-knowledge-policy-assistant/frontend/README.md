# Policy Assistant frontend

React and Vite client for the Internal Knowledge Policy Assistant API.

## Run locally

Start the FastAPI application on port 8000, then run:

```bash
npm install
npm run dev
```

Open the URL printed by Vite. During development, requests to `/api` are proxied
to `http://127.0.0.1:8000`.

For a separately hosted API, create `.env.local`:

```text
VITE_API_BASE_URL=https://your-api.example.com
```

The separately hosted API must allow the frontend origin through CORS.
