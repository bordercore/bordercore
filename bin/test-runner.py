#
# Insure that the bin directory from your virtualenv is in your PATH,
#  since this is where pytest will be found.

import argparse
import datetime
import getpass
import os
import pathlib
import sys
import xml.etree.ElementTree as ET
from subprocess import PIPE, STDOUT, Popen

import django

from lib.time_utils import convert_seconds

django.setup()

from metrics.models import Metric, MetricData  # isort:skip


TEST_REPORT = f"/tmp/test_report-{getpass.getuser()}.xml"
COVERAGE_REPORT = f"/tmp/coverage-{getpass.getuser()}.xml"


def parse_test_report(test_type, test_output=None):

    root = ET.parse(TEST_REPORT).getroot()

    test_results = {
        "test_failures": root.get("failures"),
        "test_errors": root.get("errors"),
        "test_skipped": root.get("skipped"),
        "test_count": root.get("tests"),
        "test_time_elapsed": convert_seconds(int(float(root.get("time")))),
        "test_output": test_output
    }

    test_runtime = datetime.datetime.fromtimestamp(pathlib.Path(TEST_REPORT).stat().st_mtime)

    metric = Metric.objects.get(name=test_type)
    data = MetricData(metric=metric, value=test_results, created=test_runtime)
    data.save()


def parse_coverage_report():

    root = ET.parse(COVERAGE_REPORT).getroot()

    test_results = {
        "line_rate": root.get("line-rate"),
    }

    test_runtime = datetime.datetime.fromtimestamp(int(root.get("timestamp")) / 1000)
    metric = Metric.objects.get(name="Bordercore Test Coverage")
    data = MetricData(metric=metric, value=test_results, created=test_runtime)
    data.save()


def run_test(test, coverage_count, verbose=False):

    if test == "unit":

        args = {
            "name": "Bordercore Unit Tests",
            "command": [
                "pytest",
                "-n",
                "5",
                "-m",
                "not data_quality and not functional",
                f"--junitxml={TEST_REPORT}",
                f"{os.environ.get('BORDERCORE_HOME')}/"
            ]
        }

        if coverage_count:
            args["command"].extend(
                [
                    f"--cov={os.environ.get('BORDERCORE_HOME')}",
                    f"--cov-report=xml:{COVERAGE_REPORT}",
                    f"--cov-config={os.environ.get('BORDERCORE_HOME')}/../.coveragerc"
                ]
            )

    elif test == "coverage":

        args = {
            "name": "Bordercore Coverage Report",
            "command": [
                "pytest",
                "-n",
                "5",
                "-m",
                "not data_quality",
                f"{os.environ.get('BORDERCORE_HOME')}/",
                f"--cov={os.environ.get('BORDERCORE_HOME')}",
                "--cov-report=html",
                f"--cov-config={os.environ.get('BORDERCORE_HOME')}/../.coveragerc"
            ]
        }

    elif test == "functional":

        args = {
            "name": "Bordercore Functional Tests",
            "command": [
                "pytest",
                "-m",
                "functional",
                f"--junitxml={TEST_REPORT}",
                f"{os.environ.get('BORDERCORE_HOME')}/"
            ]
        }

    elif test == "wumpus":

        args = {
            "name": "Bordercore Wumpus Tests",
            "command": [
                "pytest",
                "-m",
                "wumpus",
                f"--junitxml={TEST_REPORT}",
                f"{os.environ.get('BORDERCORE_HOME')}/"
            ]
        }

    elif test == "data":

        args = {
            "name": "Bordercore Data Quality Tests",
            "command": [
                "pytest",
                "-n",
                "3",
                "-m",
                "not wumpus and data_quality",
                f"--junitxml={TEST_REPORT}",
                f"{os.environ.get('BORDERCORE_HOME')}/"
            ]
        }

    else:
        raise ValueError(f"Unknown test type: {test}")

    if verbose:
        print(f"Running test {args['name']}")

    out = Popen(args["command"], stderr=STDOUT, stdout=PIPE)
    test_output, return_code = out.communicate()[0], out.returncode

    parse_test_report(args["name"], str(test_output))

    if test == "unit" and coverage_count:
        parse_coverage_report()

    return return_code


if __name__ == "__main__":

    for env in ("BORDERCORE_HOME",):
        if env not in os.environ:
            raise TypeError(f"{env} not found in the environment")

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-t", "--test", help="The test to run.", required=True)
    parser.add_argument("-c", "--coverage-count", help="Calculate test coverage count.", action="store_true")
    parser.add_argument("-v", "--verbose", help="Increase verbosity.", action="store_true")
    args = parser.parse_args()

    test = args.test
    verbose = args.verbose

    if args.coverage_count and "unit" not in test:
        raise ValueError("You must specify test type 'unit' for test coverage counts")

    return_code = run_test(test, args.coverage_count, verbose)
    sys.exit(return_code)
