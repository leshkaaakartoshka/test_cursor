## CPQ Frontend (Vite + React + TS)

Single-page form to submit corrugated-box quote requests to backend API and display resulting PDF link.

### Requirements

- Node 20+
- Env var: `VITE_API_BASE` (e.g., `https://api.example.com`)

### Setup

```bash
npm install
echo "VITE_API_BASE=https://api.example.com" > .env.local
npm run dev
```

Open http://localhost:5173

### Build

```bash
npm run build && npm run preview
```

### Tests

```bash
npm run test
```

### Notes

- Tailwind CSS for styling; form a11y via labels, aria-invalid, keyboard nav
- Client-side validation via Zod; analytics via dataLayer events
