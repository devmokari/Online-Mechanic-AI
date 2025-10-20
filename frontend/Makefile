.PHONY: install serve build deploy clean format lint

install:
	npm install

serve:
	npm run dev -- --host

build:
	npm run build

deploy:
	echo "Sync the dist/ folder to your hosting bucket"

clean:
	npm run clean

format:
	npm run format

lint:
	npx eslint src --ext .jsx,.js || true
