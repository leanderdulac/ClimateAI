import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { LanguageProvider } from '@/contexts/LanguageContext';
import faqpage from '../../../docs/geo/schema/faqpage.json';
import { WelcomePage } from './Welcome';

function renderWelcome() {
  return render(
    <LanguageProvider>
      <MemoryRouter>
        <WelcomePage />
      </MemoryRouter>
    </LanguageProvider>
  );
}

describe('Welcome FAQ', () => {
  it('renders a visible FAQ section matching the FAQPage schema', () => {
    renderWelcome();

    expect(screen.getByRole('heading', { name: 'Perguntas frequentes' })).toBeInTheDocument();

    for (const question of faqpage.mainEntity) {
      expect(screen.getByText(question.name)).toBeInTheDocument();
      expect(screen.getByText(question.acceptedAnswer.text)).toBeInTheDocument();
    }
  });
});
