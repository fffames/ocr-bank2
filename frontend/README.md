# OCR Bank Frontend

React + TypeScript frontend for bank receipt OCR and RAG chatbot.

## Setup

1. **Install dependencies:**
```bash
npm install
```

2. **Configure environment:**
```bash
cp .env.example .env
```

3. **Start development server:**
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Tech Stack

- React 18 with TypeScript
- Vite (build tool)
- React Router (routing)
- Axios (HTTP client)
- Tailwind CSS (styling)
- React Query (data fetching)
- React Hook Form (forms)
- Zod (validation)
- Recharts (charts)
- Lucide React (icons)

## Project Structure

```
src/
├── pages/              # Page components
├── components/         # Reusable components
├── services/           # API service layer
├── hooks/              # Custom React hooks
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
├── App.tsx             # Main app component
└── main.tsx            # Entry point
```
