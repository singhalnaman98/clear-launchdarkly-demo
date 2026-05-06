import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styles from './LoginPage.module.css'

export default function LoginPage() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleLogin = async (event) => {
    event.preventDefault()
    setError(null)

    if (!username.trim()) {
      setError('Username is required.')
      return
    }

    if (!password.trim()) {
      setError('Password is required.')
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch(`http://localhost:8000/api/user?user_id=${encodeURIComponent(username)}`)
      if (!response.ok) {
        throw new Error(`Login request failed: ${response.status}`)
      }

      const userData = await response.json()
      navigate('/subscribe', { state: { user: userData } })

    } catch (fetchError) {
      setError(fetchError.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.logo}>CLEA<span>R</span></div>
        <h1>Login</h1>
        <p className={styles.subtitle}>Please enter your username and password to login.</p>
        <form className={styles.form} onSubmit={handleLogin}>
          <label>
            Username
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              type="text"
              name="username"
              placeholder="username"
              autoComplete="username"
            />
          </label>

          <label>
            Password
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              name="password"
              placeholder="password"
              autoComplete="current-password"
            />
          </label>

          {error && <div className={styles.error}>{error}</div>}

          <div className={styles.actions}>
            <button className={styles.primary} type="submit" disabled={isLoading}>
              {isLoading ? 'Logging in…' : 'Login'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
