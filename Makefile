EC2=ec2:/var/www/django/static/
MAX_AGE=2592000
ELASTICSEARCH_INDEX_TEST=bordercore_test
ELASTICSEARCH_ENDPOINT_TEST=http://localhost:9201
MAPPINGS=$(BORDERCORE_HOME)/../config/elasticsearch/mappings.json


export env_var := MyEnvVariable

install:
	pip install --upgrade pip && pip install -r requirements.txt

.ONESHELL:
.SILENT:
webpack: webpack_build webpack_ec2

webpack_build: check-env
	cd $(BORDERCORE_HOME)
	npm run dev &&
	npm run build

webpack_ec2: check-env
	cd $(BORDERCORE_HOME)
	rsync -azv --delete static/ $(EC2)
	scp ./webpack-stats.json $(EC2)../bordercore/bordercore

check-env:
ifndef BORDERCORE_HOME
	$(error BORDERCORE_HOME is undefined)
endif

test:
	python -m pytest -vv --cov=lib --cov=cli tests/*.py

test_data:
	python3 $(BORDERCORE_HOME)/../bin/test-runner.py --test data

test_unit:
	ELASTICSEARCH_INDEX=$(ELASTICSEARCH_INDEX_TEST) ELASTICSEARCH_ENDPOINT=$(ELASTICSEARCH_ENDPOINT_TEST) \
	python3 $(BORDERCORE_HOME)/../bin/test-runner.py --test unit

test_wumpus:
	python3 $(BORDERCORE_HOME)/../bin/test-runner.py --test wumpus

test_functional: reset_elasticsearch
# Configure functional tests to use a test instance of Elasticsearch. Don't use production.
	ELASTICSEARCH_INDEX=$(ELASTICSEARCH_INDEX_TEST) ELASTICSEARCH_ENDPOINT=$(ELASTICSEARCH_ENDPOINT_TEST) \
	python3 $(BORDERCORE_HOME)/../bin/test-runner.py --test functional

test_coverage:
	ELASTICSEARCH_INDEX=$(ELASTICSEARCH_INDEX_TEST) ELASTICSEARCH_ENDPOINT=$(ELASTICSEARCH_ENDPOINT_TEST) \
	python3 $(BORDERCORE_HOME)/../bin/test-runner.py --test coverage


reset_elasticsearch:
# Delete the Elasticsearch test instance and re-populate its mappings
	curl --no-progress-meter -XDELETE "$(ELASTICSEARCH_ENDPOINT_TEST)/$(ELASTICSEARCH_INDEX_TEST)/" > /dev/null
	curl --no-progress-meter -XPUT $(ELASTICSEARCH_ENDPOINT_TEST)/$(ELASTICSEARCH_INDEX_TEST) -H "Content-Type: application/json" -d @$(MAPPINGS) > /dev/null
