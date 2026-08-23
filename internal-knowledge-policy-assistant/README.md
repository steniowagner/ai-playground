# Internal Knowledge Policy Assistant

The application runs as two containers:

- `api`: FastAPI, retrieval, embeddings, and answer generation
- `frontend`: React application served by Nginx

## Configuration

Create `agent/.env` with the credentials used by the configured providers:

```text
GROQ_API_KEY=your-groq-api-key
HF_TOKEN=your-hugging-face-token
```

Do not commit this file. The backend Docker build excludes it from the image.

## Run with Docker Compose

From this directory, run:

```bash
docker compose up --build
```

Then open:

- Frontend: http://localhost:3000
- API documentation: http://localhost:8000/docs

The first backend startup can take longer while it downloads the Hugging Face
model. Docker stores that download in the `huggingface-cache` volume for later
runs.

Stop the services with:

```bash
docker compose down
```

To also delete the downloaded model cache:

```bash
docker compose down --volumes
```
