import { lazy, Suspense, useState } from 'react';
import { MessageCircle } from 'lucide-react';

import { Button } from './ui/button';

const ClimateAssistant = lazy(() =>
  import('./ClimateAssistant').then((module) => ({ default: module.ClimateAssistant }))
);

export function ClimateAssistantLauncher() {
  const [isMounted, setIsMounted] = useState(false);

  if (!isMounted) {
    return (
      <Button
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg z-50 bg-primary hover:bg-primary/90 transition-all duration-300 hover:scale-110"
        onClick={() => setIsMounted(true)}
        data-testid="climate-assistant-trigger"
      >
        <MessageCircle className="h-8 w-8 text-white" />
      </Button>
    );
  }

  return (
    <Suspense fallback={null}>
      <ClimateAssistant defaultOpen />
    </Suspense>
  );
}