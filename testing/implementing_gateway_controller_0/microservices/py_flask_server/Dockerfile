FROM python:3.11-slim
WORKDIR /app
COPY ./flask_server.py .
RUN pip install flask
EXPOSE 30080
CMD ["python3", "flask_server.py"]