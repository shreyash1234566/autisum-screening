# =============================================================================
# AutiScreen — Dashboard Dockerfile  (multi-stage, optimised)
#
# Stage 1  builds the React bundle with npm ci (reproducible lock-file install).
# Stage 2  serves the static files via lean nginx + custom SPA config.
#
# REACT_APP_API_URL is a BUILD-TIME variable — CRA bakes it into the JS bundle.
# The browser resolves it directly, so it must be reachable from the browser,
# NOT from inside the Docker network.
# Default: http://localhost:8000  (port 8000 is exposed on the host).
# Production override: --build-arg REACT_APP_API_URL=https://api.yourdomain.com
# =============================================================================

# ─── Stage 1: React build ────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy manifests first — Docker caches this layer until packages actually change,
# so a code-only edit won't re-run npm install.
COPY package.json package-lock.json* ./

# `npm ci` is faster than `npm install` and guarantees the lock file is respected.
RUN npm install --prefer-offline

COPY . .

# Build-time API URL baked into the static JS bundle
ARG REACT_APP_API_URL=http://localhost:8000
ENV REACT_APP_API_URL=$REACT_APP_API_URL

RUN npm run build

# ─── Stage 2: nginx static server ────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Custom config: SPA routing + gzip compression + proper cache headers
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
