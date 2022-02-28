S3=s3://bordercore-blobs/django
MAX_AGE=2592000
ELASTICSEARCH_INDEX_TEST=bordercore_test
ELASTICSEARCH_ENDPOINT_TEST=http://localhost:9201
MAPPINGS=$(BORDERCORE_HOME)/../config/elasticsearch/mappings.json


export env_var := MyEnvVariable

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
	aws s3 cp static/dist/css/theme-dark.css $(S3)/css/ --cache-control max-age=$(MAX_AGE) &&
	aws s3 cp static/dist/css/theme-dark.min.css $(S3)/css/ --cache-control max-age=$(MAX_AGE) &&
	aws s3 cp static/dist/css/theme-light.css $(S3)/css/ --cache-control max-age=$(MAX_AGE) &&
	aws s3 cp static/dist/css/theme-light.min.css $(S3)/css/ --cache-control max-age=$(MAX_AGE) &&
	aws s3 cp static/dist/css/vue-sidebar-menu.min.css $(S3)/css/ --cache-control max-age=$(MAX_AGE) &&
	aws s3 cp static/dist/js/javascript-bundle.js.gz $(S3)/js/ --cache-control max-age=$(MAX_AGE) --content-encoding gzip &&
	aws s3 cp static/dist/js/javascript-bundle.min.js.gz $(S3)/js/ --cache-control max-age=$(MAX_AGE) --content-encoding gzip

check-env:
ifndef BORDERCORE_HOME
	$(error BORDERCORE_HOME is undefined)
endif

test:
	python -m pytest -vv --cov=lib --cov=cli tests/*.py

test_data:
	$(VIRTUALENV)python3 $(BORDERCORE_HOME)/../bin/test-runner.py --test-list data

test_unit:
	ELASTICSEARCH_INDEX=$(ELASTICSEARCH_INDEX_TEST) ELASTICSEARCH_ENDPOINT=$(ELASTICSEARCH_ENDPOINT_TEST) \
	$(VIRTUALENV)python3 $(BORDERCORE_HOME)/../bin/test-runner.py --test-list unit --coverage-count

test_wumpus:
	$(VIRTUALENV)python3 $(BORDERCORE_HOME)/../bin/test-runner.py --test-list wumpus

test_functional: reset_elasticsearch
# Configure functional tests to use a test instance of Elasticsearch. Don't use production.
	ELASTICSEARCH_INDEX=$(ELASTICSEARCH_INDEX_TEST) ELASTICSEARCH_ENDPOINT=$(ELASTICSEARCH_ENDPOINT_TEST) \
	$(VIRTUALENV)python3 $(BORDERCORE_HOME)/../bin/test-runner.py --test-list functional

test_coverage:
	ELASTICSEARCH_INDEX=$(ELASTICSEARCH_INDEX_TEST) ELASTICSEARCH_ENDPOINT=$(ELASTICSEARCH_ENDPOINT_TEST) \
	$(VIRTUALENV)python3 $(BORDERCORE_HOME)/../bin/test-runner.py --test-list coverage


reset_elasticsearch:
# Delete the Elasticsearch test instance and re-populate its mappings
	curl --no-progress-meter -XDELETE "$(ELASTICSEARCH_ENDPOINT_TEST)/$(ELASTICSEARCH_INDEX_TEST)/" > /dev/null
	curl --no-progress-meter -XPUT $(ELASTICSEARCH_ENDPOINT_TEST)/$(ELASTICSEARCH_INDEX_TEST) -H "Content-Type: application/json" -d @$(MAPPINGS) > /dev/null
