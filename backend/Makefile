.PHONY: install run build package deploy clean lint

install:
	pip install -r requirements.txt

run:
	python lambda_function.py

build:
	mkdir -p build
	pip install --target build -r requirements.txt
	cp -r lambda_function.py utils build/

package: build
	cd build && zip -r ../lambda_package.zip .

deploy: package
	aws lambda update-function-code \
	--function-name mechanic-ai-lambda \
	--zip-file fileb://lambda_package.zip

clean:
	rm -rf build lambda_package.zip

lint:
	python -m compileall lambda_function.py utils
