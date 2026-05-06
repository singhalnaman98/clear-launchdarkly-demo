import React from 'react'
import styles from './PlanCard.module.css'

export default function PlanCard({ plan, selected, highlightedPlan, onSelect }) {
  return (
    <div
      className={`${styles.card} ${selected ? styles.featured : ''} ${selected ? styles.selected : ''}`}
      onClick={() => onSelect(plan.id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onSelect(plan.id)}
    >
      <div className={styles.info}>
        <div className={styles.name}>{plan.name}</div>
        <div className={styles.desc}>{plan.desc}</div>
        {plan.badge && (
          <span className={`${styles.badge} ${styles[`badge_${plan.badge.type}`]}`}>
            {plan.badge.text}
          </span>
        )}
      </div>
      <div className={styles.pricing}>
        <div className={styles.price}>{plan.price}</div>
        <div className={styles.period}>{plan.period}</div>
        {plan.was && <div className={styles.was}>{plan.was}</div>}
      </div>
      {selected && <div className={styles.checkmark}>✓</div>}
    </div>
  )
}
