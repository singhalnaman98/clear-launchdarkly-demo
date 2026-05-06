import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import PlanCard from './PlanCard'
import ChatWidget from './ChatWidget'
import styles from './SubscriptionPage.module.css'
import { useBoolVariation, useStringVariation, useLDClient } from '@launchdarkly/react-sdk'


export default function SubscriptionPage() {
  
  const flexEnabled = useBoolVariation('flex-subscription-enabled', false)
  const highlightedPlan = useStringVariation('highlighted-plan-variant', 'none')
  console.log('Flex Subscription Enabled:', flexEnabled)
  console.log('Highlighted Plan:', highlightedPlan)
  const location = useLocation()
  const user = location.state?.user

  const ldClient = useLDClient()
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [plansData, setPlansData] = useState({
    annualPlan: null,
    flexPlans: [],
  })
  const [plansError, setPlansError] = useState(null)
  const [selectionMessage, setSelectionMessage] = useState('')
  const [ldContextReady, setLdContextReady] = useState(false)

  useEffect(() => {
    if (!ldContextReady) return
    if (highlightedPlan !== 'none' && !flexEnabled) {
      alert(`Configuration error: highlighted-plan-variant is set to "${highlightedPlan}" but flex-subscription-enabled is off. The highlighted plan will have no effect.`)
      return
    }
    if (highlightedPlan !== 'none') {
      setSelectedPlan(highlightedPlan)
    } else if (selectedPlan && highlightedPlan === 'none') {
      setSelectedPlan(null)
    }
  }, [highlightedPlan, flexEnabled, ldContextReady])

  // Custom onSelect that allows overriding flag-based selection
  const handlePlanSelect = (planId) => {
    setSelectedPlan(planId)
  }

  useEffect(() => {
    let isMounted = true

    const url = new URL('http://localhost:8000/api/plans')
    if (user?.user_id) {
      url.searchParams.append('user_id', user.user_id)
    }

    fetch(url.toString())
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Failed to load plans: ${res.status}`)
        }
        return res.json()
      })
      .then((data) => {
        if (!isMounted) return

        const annualPlan = data?.annualPlan ?? data?.annual
        const flexPlans = data?.flexPlans ?? data?.flex_plans ?? data?.flex

        setPlansData({
          annualPlan: annualPlan?.id ? annualPlan : null,
          flexPlans: Array.isArray(flexPlans) && flexPlans.length > 0 ? flexPlans : [],
        })
        setPlansError(null)
      })
      .catch((error) => {
        if (!isMounted) return
        console.warn('Plan fetch failed.', error)
        setPlansError(error)
      })

    return () => {
      isMounted = false
    }
  }, [flexEnabled, user])

  useEffect(() => {
    const updateLDContext = async () => {
      if (ldClient && user?.user_id) {
        await ldClient.identify({
          kind: 'user',
          key: user.user_id,
          account_status: user.status,
          airport: user.airport,
        });
        console.log("LD Context updated with status:", user.status);
        setLdContextReady(true)
      }
    };
    updateLDContext();
  }, [user?.status, ldClient, user?.user_id]);

  const { annualPlan, flexPlans } = plansData
  const plans = flexEnabled ? flexPlans.filter(Boolean) : [annualPlan].filter(Boolean)

  const handleContinue = async () => {
    const planId = selectedPlan || annualPlan?.id
    const eventData = { planId }
    console.log('plan-selected event payload:', eventData)

    if (ldClient && planId) {
      try {
        console.log('Tracking LaunchDarkly event plan-selected')
        ldClient.track('plan-selected', eventData)
        console.log('Calling ldClient.flush() to send event immediately')
        await ldClient.flush()
        console.log('LaunchDarkly event flushed successfully')
      } catch (error) {
        console.error('Error tracking LaunchDarkly event', error)
      }
    }

    setSelectionMessage(`Plan selected: ${planId}`)
    alert(`Plan selected: ${planId}`)
  }

  return (
    <div className={styles.page}>
      {plansError && (
        <div style={{ color: '#b21f1f', marginBottom: '1rem', fontSize: '0.95rem' }}>
          Unable to load remote plan data.
        </div>
      )}

      {/* Header */}
      <header className={styles.header}>
        <div className={styles.logo}>
          CLEA<span>R</span>
        </div>
        <div className={styles.headerRight}>Membership</div>
      </header>

      {/* Hero */}
      <div className={styles.hero}>
        <div className={styles.eyebrow}>TSA PreCheck + Airport Access</div>
        <h1 className={styles.title}>
          {user ? (
            user.status === 'expired' ?
              `Welcome back, ${user.user_id}. We're excited for you to resume your subscription. Check out these plans:` :
            user.status === 'free' ?
              `Welcome ${user.user_id}. We're excited for you to join Clear. Check out these plans:` :
              `Welcome back, ${user.user_id}.`
          ) : flexEnabled ?
            'Flexible plans, built around your travel' :
            'Choose your CLEAR membership'}
        </h1>
        <p className={styles.subtitle}>
          {user ? (
            user.status === 'expired' ?
              'Your membership has room to grow — pick the right plan and jump back in.' :
            user.status === 'free' ?
              'Start with any of these flexible plans and get travel-ready with CLEAR.' :
              'Here are your personalized plan options.'
          ) : flexEnabled ?
            'New — subscribe by the day, week, or month. No annual commitment needed.' :
            'Fast, contactless identity verification at 50+ airports nationwide.'}
        </p>
        {flexEnabled && (
          <div className={styles.newBadge}>New feature</div>
        )}
      </div>

      {/* Plans */}
      <div className={styles.plans}>
        {plans.map((plan, i) => (
          <div key={plan.id} style={{ animationDelay: `${i * 0.06}s` }}>
            <PlanCard
              plan={plan}
              selected={selectedPlan === plan.id}
              highlightedPlan={highlightedPlan}
              onSelect={handlePlanSelect}
            />
          </div>
        ))}
      </div>

      {/* CTA */}
      <div className={styles.ctaWrap}>
        <button
          className={styles.cta}
          disabled={flexEnabled && !selectedPlan}
          onClick={handleContinue}
        >
          {flexEnabled
            ? selectedPlan
              ? `Continue with ${plans.find((p) => p.id === selectedPlan)?.name}`
              : 'Select a plan to continue'
            : `Get started — ${annualPlan?.price}${annualPlan?.period}`}
        </button>
        {selectionMessage && (
          <div className={styles.selectionMessage}>{selectionMessage}</div>
        )}
        <p className={styles.legal}>
          Cancel anytime · Secure checkout · No hidden fees
        </p>
      </div>
      {user?.user_id && <ChatWidget user_id={user.user_id} />}
    </div>
  )
}
