# Start everything
up:
	docker compose up -d --build

# Stop everything
down:
	docker compose down

# Restart everything (the one you want!)
restart:
	docker compose down
	docker compose up -d --build

# See logs
logs:
	docker compose logs -f