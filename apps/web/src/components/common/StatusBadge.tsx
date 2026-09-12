import React from 'react';
import { RiskTier } from '../../types';

interface StatusBadgeProps {
  tier: RiskTier;
  score?: number;
  showScore?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ tier, score, showScore = false }) => {
  const tierClass = tier.toLowerCase();
  
  return (
    <span className={`badge-risk ${tierClass}`}>
      <span className={`pulse-dot ${tierClass}`} />
      {tier}
      {showScore && score !== undefined && ` (${score.toFixed(1)})`}
    </span>
  );
};
