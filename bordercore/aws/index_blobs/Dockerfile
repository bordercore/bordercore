FROM public.ecr.aws/lambda/python:3.8

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
RUN mkdir ${LAMBDA_TASK_ROOT}/lib
COPY lib/util.py ${LAMBDA_TASK_ROOT}/lib/
COPY lib/elasticsearch_indexer.py ${LAMBDA_TASK_ROOT}/lib/
COPY index_blobs_lambda.py ${LAMBDA_TASK_ROOT}

# Copy static ffmpeg binary
COPY ffmpeg-6.0-amd64-static/ffprobe /usr/local/bin

# Set the CMD to your handler
CMD [ "index_blobs_lambda.handler" ]
