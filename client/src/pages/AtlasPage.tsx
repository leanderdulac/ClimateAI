import { useState } from 'react';
import { DashboardLayout } from '@/components/DashboardLayout';
import { AtlasDashboardPanel } from '@/components/AtlasDashboardPanel';
import { useTranslation } from '@/hooks/useTranslation';

export default function AtlasPage() {
  const { t } = useTranslation();

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6 space-y-6">
        <AtlasDashboardPanel />
      </div>
    </DashboardLayout>
  );
}
