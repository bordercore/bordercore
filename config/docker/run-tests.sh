# Pull the latest repo changes and run all unit and functional tests

cd /bordercore
git pull
make test_unit test_functional
