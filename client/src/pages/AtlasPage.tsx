import { DashboardLayout } from '@/components/DashboardLayout';
import { AtlasDashboardPanel } from '@/components/AtlasDashboardPanel';

export default function AtlasPage() {

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6 space-y-6">
        <AtlasDashboardPanel />
      </div>
    </DashboardLayout>
  );
}
