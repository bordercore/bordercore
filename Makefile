S3=s3://bordercore-blobs/django

install:
	pip install --upgrade pip && pip install -r requirements.txt

.ONESHELL:
.SILENT:
webpack: webpack_build webpack_aws

webpack_build: check-env
	cd $(BORDERCORE_HOME)
	npm run dev &&
	npm run build

webpack_aws: check-env
	cd $(BORDERCORE_HOME)
	aws s3 cp static/dist/css/theme-dark.css $(S3)/css/ &&
	aws s3 cp static/dist/css/theme-dark.min.css $(S3)/css/ &&
	aws s3 cp static/dist/css/theme-light.css $(S3)/css/ &&
	aws s3 cp static/dist/css/theme-light.min.css $(S3)/css/ &&
	aws s3 cp static/dist/css/vue-sidebar-menu.min.css $(S3)/css/ &&
	aws s3 cp static/dist/js/javascript-bundle.js.gz $(S3)/js/ --content-encoding gzip &&
	aws s3 cp static/dist/js/javascript-bundle.min.js.gz $(S3)/js/ --content-encoding gzip

check-env:
ifndef BORDERCORE_HOME
	$(error BORDERCORE_HOME is undefined)
endif

test:
	python -m pytest -vv --cov=lib --cov=cli tests/*.py
#	python -m pytest --nbval-lax notebook.ipynb

test_data:
	$(VIRTUALENV)python3 $(BORDERCORE_HOME)/../bin/test-runner.py --test-list data

test_unit:
	$(VIRTUALENV)python3 $(BORDERCORE_HOME)/../bin/test-runner.py --test-list unit --coverage

test_wumpus:
	$(VIRTUALENV)python3 $(BORDERCORE_HOME)/../bin/test-runner.py --test-list wumpus

test_functional:
	$(VIRTUALENV)python3 $(BORDERCORE_HOME)/../bin/test-runner.py --test-list functional

lint:
	pylint --disable=R,C hello cli

all: install lint test
