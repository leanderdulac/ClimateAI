import { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';

import { features, type FeatureName } from '@/lib/features';

interface FeatureGateProps {
  feature: FeatureName;
  children: ReactNode;
}

export function FeatureGate({ feature, children }: FeatureGateProps) {
  if (!features[feature]) {
    return <Navigate to="/dashboard" replace />;
  }
  return <>{children}</>;
}
