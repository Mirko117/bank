COMPOSE = docker compose --env-file .env.docker

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

local:
	docker stop nginx_proxy flask_app

restart:
	$(COMPOSE) down
	$(COMPOSE) up -d

logs:
	$(COMPOSE) logs -f