import React from 'react'
import SubscriptionPage from './components/SubscriptionPage'
import LoginPage from './components/LoginPage'
import { useInitializationStatus } from '@launchdarkly/react-sdk'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

export default function App() {
  const { status, error } = useInitializationStatus()
  if (status === 'initializing') return <div> initializing </div>
  if (status === 'failed') return <div> Error: {error?.message} </div>

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/subscribe" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/subscribe"
          element={
            <div style={{ marginTop: '1rem' }}>
              <SubscriptionPage />
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

