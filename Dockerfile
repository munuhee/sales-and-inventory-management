FROM python:3.10.12-alpine
WORKDIR /sales-and-inventory-management
COPY . /sales-and-inventory-management
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
