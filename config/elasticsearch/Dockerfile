FROM elasticsearch:7.16.2

ENV ES_JAVA_OPTS="-Xms512m -Xmx512m"

# This disables a security warning.
ENV ES_SETTING_XPACK_SECURITY_ENABLED="false"

RUN /usr/share/elasticsearch/bin/elasticsearch-plugin install --batch ingest-attachment
