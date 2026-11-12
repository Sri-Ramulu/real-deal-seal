FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY data_platform/ data_platform/
COPY api/ api/
COPY docs/evidence/ docs/evidence/
COPY samples/ samples/
COPY scripts/ scripts/
COPY sdk/ sdk/
COPY --from=web /web/build web/build
# Build the warehouse at image build time: a red gate fails the deploy instead of serving bad data.
# At runtime the API rebuilds it under RDS_VAR_DIR from landing plus the operational extract; mount a disk there to keep accounts and orders.
RUN python data_platform/run/build.py
ENV RDS_VAR_DIR=/var/rds
EXPOSE 8000
CMD ["sh", "-c", "uvicorn rds.main:app --app-dir api --host 0.0.0.0 --port ${PORT:-8000}"]
