# syntax=docker/dockerfile:1

# ── deps: npm install layer, cached until the lockfile changes ──────────────
FROM node:22-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ── dev: Vite dev server; compose bind-mounts the source over it ────────────
FROM deps AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ── build: type-check + production bundle ───────────────────────────────────
FROM deps AS build
COPY . .
# No VITE_API_URL -> the client calls a same-origin relative /api, which the
# ALB (prod) / gateway (compose) routes to the backend. No CORS in production.
RUN npm run build

# ── prod: static bundle on nginx, no Node runtime ──────────────────────────
FROM nginx:1.27-alpine AS prod
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
