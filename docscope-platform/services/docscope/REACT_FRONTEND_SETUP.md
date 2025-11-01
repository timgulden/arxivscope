# React Frontend Setup Guide

## Current Status

The React frontend directory exists but the project hasn't been initialized yet.

## Quick Start Setup

To get the React frontend working:

### Step 1: Initialize Vite + React + TypeScript Project

```bash
cd docscope-platform/services/docscope/react

# Create a new Vite project with React + TypeScript template
npm create vite@latest . -- --template react-ts

# Answer "y" when asked if you want to overwrite files
```

### Step 2: Install Dependencies

```bash
# Install basic dependencies
npm install

# Install API integration libraries
npm install axios plotly.js react-plotly.js

# Install TypeScript types
npm install -D @types/react-plotly.js @types/plotly.js

# Optional: Install testing libraries (recommended)
npm install -D vitest @testing-library/react @testing-library/jest-dom @vitest/ui jsdom
```

### Step 3: Configure Vite for Environment Variables

Create `vite.config.ts` (or update it):

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: parseInt(process.env.NEW_UI_PORT || '3000', 10),
  },
  envPrefix: 'VITE_',
})
```

### Step 4: Create Environment Variables File

Create `.env` in this directory:

```env
# API Configuration (read from project root .env.local via docscope.sh)
# This will be set by docscope.sh script
VITE_API_BASE_URL=http://localhost:5001
```

### Step 5: Update package.json scripts (if needed)

The default Vite template should already have:
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }
}
```

## Test the Setup

```bash
# From project root
./docscope.sh start

# Or manually
cd docscope-platform/services/docscope/react
npm run dev
```

The frontend should start on port 3000 and be accessible at `http://localhost:3000`

## Next Steps

1. Create a basic API client in `src/services/api.ts`
2. Create basic components in `src/components/`
3. Set up routing if needed
4. Integrate with the DocTrove API

See the documentation in `docs/DEVELOPMENT/REACT_TS_GUIDE.md` for architecture patterns.
