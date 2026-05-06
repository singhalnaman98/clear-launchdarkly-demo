import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { useInitializationStatus, createLDReactProvider } from '@launchdarkly/react-sdk';


const LDProvider = createLDReactProvider(import.meta.env.VITE_LD_CLIENT_KEY, { kind: 'user', anonymous: true });

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <LDProvider>
      <App />
    </LDProvider>
  </React.StrictMode>
)
