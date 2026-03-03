FROM python:3.10

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir django djangorestframework requests

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:4000"]