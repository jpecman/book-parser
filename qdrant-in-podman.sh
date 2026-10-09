podman run --name qdrant --restart unless-stopped \
  -v qdrant_storage:/qdrant/storage \
  -p 127.0.0.1:${QDRANT_HTTP_PORT:-6333}:6333 \
  -p 127.0.0.1:${QDRANT_GRPC_PORT:-6334}:6334 \
  -d docker.io/qdrant/qdrant:latest
