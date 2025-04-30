# Use official lightweight Python image
FROM --platform=linux/amd64 python:3.12

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_NO_CUDA=1


# Set working directory
WORKDIR /app


ENV TMPDIR=/app/tmp
RUN mkdir -p /app/tmp /app/pipcache



RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*
RUN apt-get update --allow-releaseinfo-change

RUN apt-get install -y libpq-dev



#COPY Pipfile Pipfile.lock /app/
COPY requirements.txt /app/

RUN pip install --upgrade pip 
RUN pip config set global.index-url https://pypi.org/simple

RUN pip install --cache-dir=/app/pipcache --no-cache-dir -r requirements.txt

COPY ./vectorexp/ .

#RUN python manage.py runserver 0.0.0.0:8000
#CMD ["gunicorn", "vectorexp.wsgi:application", "--bind", "0.0.0.0:8000"]
CMD ["gunicorn", "vectorexp.wsgi:application", "--bind", "0.0.0.0:8000", "--workers=5", "--timeout=2000"]