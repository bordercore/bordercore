docker build \
       --build-arg git_host=$GIT_HOST \
       --build-arg git_password=$GIT_PASSWORD \
       --build-arg database_password=$DATABASE_PASSWORD \
       --build-arg secret_key=$SECRET_KEY \
       . \
       -t bordercore-testing
