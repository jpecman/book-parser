podman run --name qdrant --restart unless-stopped \
  -e QDRANT__SERVICE__API_KEY="${QDRANT_API_KEY:?set QDRANT_API_KEY in .env}" \
  -v qdrant_storage:/qdrant/storage \
  -p 127.0.0.1:${QDRANT_HTTP_PORT:-6333}:6333 \
  -d docker.io/qdrant/qdrant:latest
