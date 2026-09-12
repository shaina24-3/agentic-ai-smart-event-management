FROM node:20-alpine

WORKDIR /app

COPY frontend/package*.json ./frontend/

WORKDIR /app/frontend

RUN npm ci

COPY frontend/ .

# Build the production bundle. NEXT_PUBLIC_* vars are inlined at build time,
# so accept it as a build ARG (Render passes envVars through to the build).
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NODE_ENV=production

RUN npm run build

EXPOSE 3000

# Render injects a PORT environment variable that the container MUST bind to;
# it falls back to 3000 for local docker-compose where PORT is unset.
# (docker-compose overrides this CMD with "npm run dev" for local hot-reload dev.)
CMD ["sh", "-c", "npx next start -p ${PORT:-3000} -H 0.0.0.0"]