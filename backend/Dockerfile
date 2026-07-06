# Build from repo root: docker build -f backend/Dockerfile .
FROM python:3.13-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Open-source server package
COPY server/__init__.py server/db_local.py server/db_mock.py \
     server/server.py server/dashboard.html server/dashboard.css ./server/
COPY server/js/ ./server/js/

# Backend (cloud storage)
COPY backend/__init__.py backend/db.py ./backend/

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "server"]
