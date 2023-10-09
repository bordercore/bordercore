FROM public.ecr.aws/lambda/python:3.10

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Install ImageMagick
RUN yum install -y ImageMagick

# Copy function code
RUN mkdir ${LAMBDA_TASK_ROOT}/lib
COPY lib/util.py ${LAMBDA_TASK_ROOT}/lib/
COPY create-cover.sh ${LAMBDA_TASK_ROOT}
COPY create_collection_thumbnail_lambda.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "create_collection_thumbnail_lambda.handler" ]
