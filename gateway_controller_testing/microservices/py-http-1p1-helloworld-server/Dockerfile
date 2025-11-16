FROM python:3.11-slim
WORKDIR /app
COPY ./py-http1p1-helloworld-server.py .
RUN pip install flask
EXPOSE 30080
CMD ["python3", "py-http1p1-helloworld-server.py"]