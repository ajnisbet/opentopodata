build:
	docker build --tag opentopodata --file docker/Dockerfile .

run:
	docker run --rm -it --volume $(shell pwd)/data:/app/data:ro -p 5000:5000 opentopodata 

test: build
	docker run --rm -it -e DISABLE_MEMCACHE=1 --volume $(shell pwd)/htmlcov:/app/htmlcov opentopodata pytest --ignore=data --ignore=scripts --cov=opentopodata --cov-report html

run-local:
	FLASK_APP=opentopodata/api.py FLASK_DEBUG=1 flask run --port 5000

black:
	black --target-version py37 tests opentopodata
