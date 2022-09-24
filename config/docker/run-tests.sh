# Pull the latest repo changes and run all unit and functional tests

cd /bordercore

# Hard reset the HEAD, in case upstream history has changed
git fetch --all
git reset --hard origin/master

make test_unit test_functional
