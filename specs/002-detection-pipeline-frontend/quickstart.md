# Frontend Quickstart Guide

**Feature**: Detection Pipeline Frontend
**Branch**: `002-detection-pipeline-frontend`

---

## 1. Local Development Setup

Follow these steps to run the Next.js frontend application locally.

### 1.1 Installation
Navigate to the `frontend/` directory and install the dependencies:

```bash
cd frontend
npm install
```

### 1.2 Development Server
Start the Next.js local development server:

```bash
npm run dev
```
The application runs locally at `http://localhost:3000`.

---

## 2. OpenAPI Codegen (Cross-Service Typed Contracts)

To synchronize backend schema changes with TypeScript models, regenerate the typed OpenAPI client using the OpenAPI CLI tool:

```bash
# 1. Ensure backend service is running locally on port 8000
# 2. Run codegen script from frontend root
npm run api-generate
```

This triggers the following command under the hood:
```bash
npx openapi-typescript http://localhost:8000/openapi.json --output ./services/api.ts
```

All API request handlers and hooks import types directly from `services/api.ts`.

---

## 3. Localization (next-intl translation compilation)

Translations are placed in the `messages/` folder:
* **Vietnamese (Default)**: `messages/vi.json`
* **English**: `messages/en.json`

To check localization key completeness, compile/validate the translations:
```bash
npm run i18n-check
```

---

## 4. Linting and Formatting

We enforce ESLint rules and Prettier formatting guidelines before commits are accepted.

```bash
# Run lint checks
npm run lint

# Format code with Prettier
npx prettier --write .
```
