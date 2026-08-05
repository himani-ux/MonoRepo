import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import SafetyEvidenceDeadlineTasks from './evidence-deadline-tasks';

describe('SafetyEvidenceDeadlineTasks', () => {
  it('does not show checklist due-date details', () => {
    render(
      <SafetyEvidenceDeadlineTasks
        tasks={[
          {
            due_at: '2026-06-29 14:00',
            severity: 'INFO',
            status: 'PENDING',
            task_code: 'collect-log',
            title: 'Collect engine log',
          },
        ]}
      />,
    );

    expect(screen.getByText('Collect engine log')).toBeInTheDocument();
    expect(screen.queryByText('2026-06-29 14:00')).not.toBeInTheDocument();
    expect(screen.queryByText(/Due:/)).not.toBeInTheDocument();
  });
});
