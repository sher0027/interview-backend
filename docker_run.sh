docker compose down
docker compose build --no-cache
docker compose up -d
docker image prune -f
docker builder prune -f

sleep 10
