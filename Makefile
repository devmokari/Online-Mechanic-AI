
.PHONY: backend frontend deploy set-key create-bucket clean format

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

create-bucket:
	@if [ -z "$(BUCKET)" ]; then \
		echo "Usage: make create-bucket BUCKET=<bucket-name> [REGION=<aws-region>] [ACL=<canned-acl>]"; \
		exit 1; \
	fi
	python backend/scripts/create_s3_bucket.py $(BUCKET) --region "$(REGION)" --acl "$(ACL)"

clean:
	cd backend && make clean
	cd frontend && npm run clean

format:
	cd frontend && npm run format
