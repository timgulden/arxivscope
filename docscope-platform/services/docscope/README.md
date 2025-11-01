# React Frontend for DocTrove

This is the React + TypeScript + Vite frontend for the DocTrove system.

## Setup Instructions

To initialize this project:

```bash
# Navigate to this directory
cd docscope-platform/services/docscope/react

# Initialize Vite + React + TypeScript project
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install

# Install additional dependencies for API integration
npm install axios plotly.js react-plotly.js

# Install development dependencies
npm install -D @types/react-plotly.js

# Start development server
npm run dev
```

## Configuration

The frontend reads configuration from `.env.local` in the project root (`../../../../.env.local`):

- `VITE_API_BASE_URL`: API base URL (default: `http://localhost:5001`)
- `NEW_UI_PORT`: Frontend port (default: 3000)

## Expected Structure

Once initialized, the structure should be:

```
react/
├── src/
│   ├── components/    # React components
│   ├── hooks/         # Custom hooks
│   ├── services/      # API client
│   ├── types/         # TypeScript types
│   └── App.tsx        # Main app component
├── public/
├── package.json
├── tsconfig.json
├── vite.config.ts
└── index.html
```

## Usage

Start with the `docscope.sh` script:
```bash
cd ../../../../  # Project root
./docscope.sh start
```

Or manually:
```bash
cd docscope-platform/services/docscope/react
npm run dev
```

## Integration with API

The frontend connects to the API at the URL specified in `VITE_API_BASE_URL` environment variable.

