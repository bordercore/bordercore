FROM public.ecr.aws/lambda/python:3.10

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY snarf_favicon_lambda.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "snarf_favicon_lambda.handler" ]
