# Build the Expo web app, then serve it with Caddy (build context: frontend/).
FROM node:22-bookworm-slim AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
ARG API_URL
ARG GOOGLE_WEB_CLIENT_ID=""
ENV APP_ENV=production \
    API_URL=${API_URL} \
    GOOGLE_WEB_CLIENT_ID=${GOOGLE_WEB_CLIENT_ID} \
    EXPO_NO_TELEMETRY=1 \
    CI=1
RUN npx expo export --platform web --output-dir dist

FROM caddy:2-alpine
COPY --from=build /app/dist /srv
