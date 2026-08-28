# LifeOS Mobile

An [Expo](https://docs.expo.dev/) (React Native) client for LifeOS. It talks to
the **same FastAPI backend** as the web app — the API contract is the shared
surface, not a code package.

## What's here

| Area | |
| --- | --- |
| Router | `expo-router` (file-based, in `app/`) |
| Server state | TanStack Query |
| HTTP | axios with the web client's request/refresh interceptors, ported to async keychain storage |
| Token storage | `expo-secure-store` (iOS Keychain / Android Keystore) |

Screens: **Sign in / Register**, **Dashboard** (job-search stats + a 90-day
activity summary from `/analytics/overview`), **Applications** (filterable list),
**Application detail** (status change, interviews, notes).

## Run it

```bash
npm install
# point at a reachable backend (a LAN IP or tunnel, not localhost, for a device)
EXPO_PUBLIC_API_URL=http://192.168.1.x:8000/api npx expo start
```

Press `i` / `a` for a simulator, or scan the QR with Expo Go. With no
`EXPO_PUBLIC_API_URL` it falls back to `app.json` → `extra.apiUrl`
(`http://localhost:8000/api`, fine for the iOS simulator).

## Checks

```bash
npm run typecheck   # tsc --noEmit
npm run lint        # eslint
```

CI runs both. There is no simulator in CI, so those are the gate.
