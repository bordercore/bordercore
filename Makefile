
install:
	pip install --upgrade pip && pip install -r requirements.txt

test:
	python -m pytest -vv --cov=lib --cov=cli tests/*.py
#	python -m pytest --nbval-lax notebook.ipynb

test_data:
	$(VIRTUALENV)pytest --disable-warnings -n 3 -m "not wumpus and data_quality" $(BORDERCORE_HOME)

test_unit:
	$(VIRTUALENV)pytest -s --disable-warnings -m "not data_quality" $(BORDERCORE_HOME)

test_wumpus:
	$(VIRTUALENV)pytest --disable-warnings $(BORDERCORE_HOME)/blob/ -m wumpus

test_coverage:
	$(VIRTUALENV)pytest -m "not data_quality" --cov=$(BORDERCORE_HOME) --cov-report html --cov-config=/home/jerrell/dev/django/bordercore_project/.coveragerc -s --disable-warnings $(BORDERCORE_HOME)

lint:
	pylint --disable=R,C hello cli

all: install lint test
