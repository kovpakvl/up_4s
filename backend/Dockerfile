FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/secureoffice_backend ./secureoffice_backend

EXPOSE 8765

CMD ["python", "-m", "secureoffice_backend"]
