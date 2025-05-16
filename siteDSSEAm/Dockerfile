FROM python:3.11-slim
WORKDIR /app
COPY src/ /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["python","main.py"]
EXPOSE 8000
