.PHONY: backend frontend deploy set-key clean format

backend:
	cd backend && make build

frontend:
	cd frontend && npm run build

deploy:
	cd backend && make deploy
	cd frontend && npm run deploy

set-key:
	@echo "🔐 Updating OpenAI key..."
	aws lambda update-function-configuration \
	--function-name mechanic-ai-lambda \
	--environment "Variables={OPENAI_API_KEY=$(KEY)}"

clean:
	cd backend && make clean
	cd frontend && npm run clean

format:
	cd frontend && npm run format
