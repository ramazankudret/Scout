.PHONY: up down restart logs test-unit test-int build

up:
	docker-compose -f docker/docker-compose.yml up -d

down:
	docker-compose -f docker/docker-compose.yml down

restart: down up

logs:
	docker-compose -f docker/docker-compose.yml logs -f

build:
	docker-compose -f docker/docker-compose.yml build

test-unit:
	docker-compose -f docker/docker-compose.yml run --rm backend pytest tests/unit

test-int:
	docker-compose -f docker/docker-compose.yml run --rm backend pytest tests/integration

shell-backend:
	docker-compose -f docker/docker-compose.yml exec backend /bin/bash

db-shell:
	docker-compose -f docker/docker-compose.yml exec db psql -U scout -d scout_db
