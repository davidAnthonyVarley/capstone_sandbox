FROM python:3.11-slim
WORKDIR /app
COPY ../ .
RUN pip install flask pika
EXPOSE 3000
ENV SUB_ID=medium
CMD ["python3", "subscriber-pod.py"]
