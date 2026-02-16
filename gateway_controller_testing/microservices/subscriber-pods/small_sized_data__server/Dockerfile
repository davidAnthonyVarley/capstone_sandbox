FROM python:3.11-slim
WORKDIR /app
COPY ../ .
RUN pip install -r requirements.txt
EXPOSE 3000
ENV SUB_ID=small
CMD ["python3", "subscriber-pod.py"]
