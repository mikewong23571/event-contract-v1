# Event Contract Trading System - Frontend

React-based frontend dashboard for the Event Contract Trading System.

## Tech Stack

- **Framework**: Next.js 14.0.3 with App Router
- **Language**: TypeScript
- **Styling**: TailwindCSS 3.3.5
- **UI Components**: Headless UI + Custom components
- **Charts**: Recharts
- **HTTP Client**: Axios
- **Node.js**: 18.0+

## Installation

```bash
# Install dependencies
npm install

# or using yarn
yarn install
```

## Development

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Lint code
npm run lint

# Format code
npm run format

# Type check
npm run type-check
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── layout.tsx       # Root layout
│   │   ├── page.tsx         # Home page
│   │   └── globals.css      # Global styles
│   ├── components/          # Reusable UI components
│   │   ├── signals/         # Trading signal components
│   │   ├── charts/          # Chart components
│   │   ├── risk/            # Risk management components
│   │   ├── backtesting/     # Backtesting components
│   │   └── layout/          # Layout components
│   ├── services/            # API and WebSocket clients
│   ├── types/               # TypeScript type definitions
│   └── utils/               # Utility functions
├── tests/                   # Test files
└── public/                  # Static assets
```

## Features

- **Real-time Trading Signals**: Live probability-based signals display
- **Market Data Visualization**: Interactive charts for K-line data
- **Risk Management**: Parameter configuration and monitoring
- **Backtesting Results**: Performance analysis and reporting
- **WebSocket Integration**: Real-time data streaming
- **Responsive Design**: Mobile-friendly interface

## API Integration

The frontend connects to the backend API at `http://localhost:8000/api/v1/` and WebSocket at `ws://localhost:8000/ws/` for real-time features.

## Styling

Uses TailwindCSS with custom design system including:
- Primary colors (blue theme)
- Success/danger/warning color schemes  
- Custom components (buttons, cards, inputs)
- Responsive utilities
- Dark mode support (planned)