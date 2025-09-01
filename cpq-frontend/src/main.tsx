import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

declare global {
  interface Window { dataLayer?: unknown[] }
}

window.dataLayer = window.dataLayer || [];
window.dataLayer.push({ event: 'cpq_form_view' });

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
