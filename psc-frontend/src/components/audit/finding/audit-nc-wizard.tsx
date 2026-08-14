import { useEffect, useMemo, useState, type KeyboardEvent, type ReactNode } from 'react';
import { ArrowLeft, ArrowRight, Check, ClipboardList, Loader2, Save } from 'lucide-react';
import { Button, Badge, Card, CardContent, CardHeader, CardTitle, Input, Label, Textarea } from '@/components/ui';
import { PageHeader } from '@/components/layout/page-header';
import { RootLayout } from '@/components/layout/root-layout';
import { ErrorState } from '@/components/shared';
import { SectionSkeleton } from '@/components/shared/loading-skeleton';
import { useAuditNcClosure, useAuditRcaTemplates, useUpdateAuditNcPart } from '@/hooks/audit/use-audit-finding';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/api/client';
import { cn } from '@/lib/utils';
import { ROOT_CAUSE_CATEGORIES, type AuditNcClosure, type AuditNcPartB, type AuditNcPartC, type AuditRcaTemplate } from '@/schemas/audit/nc-closure';
import { useNcWizardStore } from '@/stores/audit/use-nc-wizard-store';

interface AuditNcWizardProps {
  findingId: string;
}

const steps = [
  'Containment',
  'Completed',
  'Method',
  'Starting Point',
  'Cause Detail',
  'Summary',
] as const;

function toInputDate(value: string | null | undefined): string {
  return value ? value.slice(0, 10) : '';
}

function fromInputDate(value: string): string | null {
  return value || null;
}

function suggestedStep(closure: AuditNcClosure): number {
  if (!closure.part_b.immediate_action_text) return 0;
  if (!closure.part_b.immediate_action_completed_at) return 1;
  if (!closure.part_c.rca_method) return 2;
  if (!closure.part_c.rca_template_id && !closure.part_c.problem_statement) return 3;
  if (!closure.part_c.why_1 && closure.part_c.root_cause_categories.length === 0) return 4;
  if (closure.part_c.root_cause_summary.length < 50) return 5;
  return 5;
}

export function AuditNcWizard({ findingId }: AuditNcWizardProps) {
  const { toast } = useToast();
  const { data: closure, isLoading, error, refetch } = useAuditNcClosure(findingId);
  const { data: templates, isLoading: templatesLoading } = useAuditRcaTemplates();
  const updatePart = useUpdateAuditNcPart(findingId);
  const { stepIndex, resetForFinding, setStepIndex } = useNcWizardStore();
  const [partB, setPartB] = useState<AuditNcPartB | null>(null);
  const [partC, setPartC] = useState<AuditNcPartC | null>(null);
  const [saveError, setSaveError] = useState('');

  useEffect(() => {
    if (!closure) return;
    setPartB({
      ...closure.part_b,
      immediate_action_completed_at: toInputDate(closure.part_b.immediate_action_completed_at),
    });
    setPartC(closure.part_c);
    resetForFinding(findingId, suggestedStep(closure));
  }, [closure, findingId, resetForFinding]);

  const selectedTemplate = useMemo(
    () => templates?.templates.find((template) => template.id === partC?.rca_template_id) || null,
    [partC?.rca_template_id, templates?.templates]
  );
  const rootCauseLength = partC?.root_cause_summary.length || 0;
  const progress = Math.round(((stepIndex + 1) / steps.length) * 100);

  const saveCurrentStep = async () => {
    if (!partB || !partC) return false;
    setSaveError('');
    try {
      if (stepIndex <= 1) {
        await updatePart.mutateAsync({
          part: 'part-b',
          data: {
            ...partB,
            immediate_action_completed_at: fromInputDate(partB.immediate_action_completed_at || ''),
          },
        });
      } else {
        await updatePart.mutateAsync({ part: 'part-c', data: partC });
      }
      toast({ title: 'NC draft saved' });
      return true;
    } catch (stepError) {
      const message = getErrorMessage(stepError);
      setSaveError(message);
      toast({
        variant: 'destructive',
        title: 'NC draft not saved',
        description: message,
      });
      return false;
    }
  };

  const goNext = async () => {
    const saved = await saveCurrentStep();
    if (saved && stepIndex < steps.length - 1) {
      setStepIndex(stepIndex + 1);
    }
  };

  const goBack = () => {
    setSaveError('');
    setStepIndex(Math.max(0, stepIndex - 1));
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const tagName = (event.target as HTMLElement).tagName;
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 's') {
      event.preventDefault();
      void saveCurrentStep();
      return;
    }
    if (event.key === 'Escape' && stepIndex > 0) {
      event.preventDefault();
      goBack();
      return;
    }
    if (event.key === 'Enter' && tagName !== 'TEXTAREA') {
      event.preventDefault();
      void goNext();
    }
  };

  if (error || (!isLoading && !closure)) {
    return (
      <RootLayout>
        <PageHeader title="NC Wizard" showBack backTo="/audit" />
        <ErrorState
          title="NC wizard not found"
          message="The finding may not be an NC, or you may not have access."
          onRetry={() => refetch()}
        />
      </RootLayout>
    );
  }

  if (isLoading || !closure || !partB || !partC) {
    return (
      <RootLayout>
        <PageHeader title="NC Wizard" showBack backTo="/audit" />
        <div className="space-y-4 p-4">
          <SectionSkeleton />
          <SectionSkeleton />
        </div>
      </RootLayout>
    );
  }

  return (
    <RootLayout>
      <PageHeader title="NC Wizard" showBack backTo="/audit" />
      <div className="grid gap-4 p-4 lg:grid-cols-[3fr_2fr]" onKeyDown={handleKeyDown}>
        <main className="space-y-4">
          <Card>
            <CardContent className="space-y-3 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={closure.part_a.nc_classification === 'MAJOR_NC' ? 'destructive' : 'warning'}>
                  {closure.part_a.nc_classification || 'NC'}
                </Badge>
                <Badge variant="secondary">{closure.car.status}</Badge>
              </div>
              <div>
                <p className="text-sm font-medium text-neutral-500">Step {stepIndex + 1} of {steps.length}</p>
                <h1 className="mt-1 text-xl font-semibold text-neutral-900">{steps[stepIndex]}</h1>
              </div>
              <div className="h-2 rounded-full bg-neutral-100" aria-label="Wizard progress">
                <div className="h-2 rounded-full bg-primary-500" style={{ width: `${progress}%` }} />
              </div>
            </CardContent>
          </Card>

          {saveError && (
            <div className="rounded-md border border-error-200 bg-error-50 p-3 text-sm text-error-700" role="alert">
              {saveError}
            </div>
          )}

          <WizardStep
            stepIndex={stepIndex}
            partB={partB}
            partC={partC}
            templates={templates?.templates || []}
            templatesLoading={templatesLoading}
            rootCauseLength={rootCauseLength}
            onPartBChange={setPartB}
            onPartCChange={setPartC}
            onSelectTemplate={(template) => {
              setPartC({
                ...partC,
                rca_template_id: template.id,
                root_cause_summary: template.template_text,
                problem_statement: partC.problem_statement || template.title,
              });
            }}
          />

          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:items-center sm:justify-between">
            <Button type="button" variant="outline" onClick={goBack} disabled={stepIndex === 0 || updatePart.isPending}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <div className="flex flex-col gap-2 sm:flex-row">
              <Button type="button" variant="outline" onClick={() => void saveCurrentStep()} disabled={updatePart.isPending}>
                {updatePart.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                Save Draft
              </Button>
              <Button type="button" onClick={() => void goNext()} disabled={updatePart.isPending}>
                {stepIndex === steps.length - 1 ? <Check className="mr-2 h-4 w-4" /> : <ArrowRight className="mr-2 h-4 w-4" />}
                {stepIndex === steps.length - 1 ? 'Save Summary' : 'Save and Continue'}
              </Button>
            </div>
          </div>
        </main>

        <aside className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <ClipboardList className="h-4 w-4" />
                NC Context
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <ContextRow label="Reference" value={closure.part_a.nc_reference_no} />
              <ContextRow label="Deadline" value={closure.part_a.required_closure_deadline || '-'} />
              <ContextRow label="Clause" value={closure.part_a.clause_ref_text || closure.part_a.rule_book_type || '-'} />
              <ContextRow label="Evidence" value={closure.part_a.objective_evidence || '-'} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Saved Answers</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <ContextRow label="Immediate Action" value={partB.immediate_action_text || '-'} />
              <ContextRow label="Completed" value={partB.immediate_action_completed_at || '-'} />
              <ContextRow label="RCA Method" value={partC.rca_method || '-'} />
              <ContextRow label="Template" value={selectedTemplate?.title || '-'} />
              <ContextRow label="Summary" value={partC.root_cause_summary || '-'} />
            </CardContent>
          </Card>
        </aside>
      </div>
    </RootLayout>
  );
}

function WizardStep({
  stepIndex,
  partB,
  partC,
  templates,
  templatesLoading,
  rootCauseLength,
  onPartBChange,
  onPartCChange,
  onSelectTemplate,
}: {
  stepIndex: number;
  partB: AuditNcPartB;
  partC: AuditNcPartC;
  templates: AuditRcaTemplate[];
  templatesLoading: boolean;
  rootCauseLength: number;
  onPartBChange: (partB: AuditNcPartB) => void;
  onPartCChange: (partC: AuditNcPartC) => void;
  onSelectTemplate: (template: AuditRcaTemplate) => void;
}) {
  if (stepIndex === 0) {
    return (
      <PromptCard
        label="What did you do first to keep the ship safe or stop the problem getting worse?"
        hint="Write the action already taken, such as isolating equipment, briefing the watch, or adding a temporary control."
      >
        <Textarea
          aria-label="Immediate action"
          value={partB.immediate_action_text}
          onChange={(event) => onPartBChange({ ...partB, immediate_action_text: event.target.value })}
          rows={7}
          data-eid="MOCKUP-NC-WIZ-05:nc_wizard_step1.immediate_action"
        />
      </PromptCard>
    );
  }

  if (stepIndex === 1) {
    return (
      <PromptCard
        label="When was that immediate action completed?"
        hint="Use the completion date recorded on board. Major NC action must be within 72 hours of issue."
      >
        <Input
          aria-label="Immediate action completed date"
          type="date"
          value={partB.immediate_action_completed_at || ''}
          onChange={(event) => onPartBChange({ ...partB, immediate_action_completed_at: event.target.value })}
          data-eid="MOCKUP-NC-WIZ-05:nc_wizard_step1.completed_at"
        />
      </PromptCard>
    );
  }

  if (stepIndex === 2) {
    return (
      <PromptCard
        label="Which RCA method did you use?"
        hint="Choose the method that best matches the discussion held with the team."
      >
        <select
          aria-label="RCA method"
          value={partC.rca_method}
          onChange={(event) => onPartCChange({ ...partC, rca_method: event.target.value })}
          className="h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          data-eid="MOCKUP-NC-WIZ-05:nc_wizard_step2.rca_method"
        >
          <option value="">Select method</option>
          <option value="FIVE_WHY">5 Why</option>
          <option value="FISHBONE_ISHIKAWA">Fishbone</option>
          <option value="STRUCTURED_NARRATIVE">Structured notes</option>
          <option value="OTHER">Other</option>
        </select>
        {partC.rca_method === 'OTHER' && (
          <Input
            aria-label="Other RCA method"
            value={partC.rca_method_other}
            onChange={(event) => onPartCChange({ ...partC, rca_method_other: event.target.value })}
          />
        )}
      </PromptCard>
    );
  }

  if (stepIndex === 3) {
    return (
      <PromptCard
        label="Pick the closest starting point for the root cause."
        hint="The selected text is copied into the summary. Edit it so it matches what happened on board."
      >
        {templatesLoading ? (
          <div className="text-sm text-neutral-500">Loading templates...</div>
        ) : (
          <div className="grid gap-3" data-eid="MOCKUP-NC-WIZ-05:nc_wizard_step3.template_carousel">
            {templates.map((template) => (
              <button
                key={template.id}
                type="button"
                onClick={() => onSelectTemplate(template)}
                className={cn(
                  'rounded-md border p-3 text-left text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                  partC.rca_template_id === template.id
                    ? 'border-primary-300 bg-primary-50 text-primary-900'
                    : 'border-neutral-200 bg-white text-neutral-800 hover:bg-neutral-50'
                )}
              >
                <span className="block font-medium">{template.title}</span>
                <span className="mt-1 block text-xs text-neutral-500">{template.category}</span>
              </button>
            ))}
          </div>
        )}
      </PromptCard>
    );
  }

  if (stepIndex === 4) {
    return (
      <PromptCard
        label="Write the reason chain and choose the cause groups."
        hint="Use short facts. Stop when the answer points to a fix that prevents repeat."
      >
        <div className="grid gap-3">
          {(['why_1', 'why_2', 'why_3', 'why_4', 'why_5'] as const).map((fieldName, index) => (
            <Input
              key={fieldName}
              aria-label={`Why ${index + 1}`}
              value={partC[fieldName]}
              onChange={(event) => onPartCChange({ ...partC, [fieldName]: event.target.value })}
              data-eid={index === 0 ? 'MOCKUP-NC-WIZ-05:nc_wizard_step3.why_inputs' : undefined}
            />
          ))}
        </div>
        <fieldset className="mt-4 space-y-2 rounded-md border border-neutral-200 p-3" data-eid="MOCKUP-NC-WIZ-05:nc_wizard_step3.rc_categories">
          <legend className="px-1 text-sm font-medium text-neutral-700">Cause groups</legend>
          <div className="grid gap-2 sm:grid-cols-2">
            {ROOT_CAUSE_CATEGORIES.map((category) => (
              <label key={category} className="flex items-center gap-2 text-sm text-neutral-700">
                <input
                  type="checkbox"
                  checked={partC.root_cause_categories.includes(category)}
                  onChange={(event) => {
                    const nextCategories = event.target.checked
                      ? [...partC.root_cause_categories, category]
                      : partC.root_cause_categories.filter((item) => item !== category);
                    onPartCChange({ ...partC, root_cause_categories: nextCategories });
                  }}
                  className="h-4 w-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                />
                {category}
              </label>
            ))}
          </div>
        </fieldset>
      </PromptCard>
    );
  }

  return (
    <PromptCard
      label="Write the final root cause summary."
      hint="Use at least 50 characters. Say what failed, why it failed, and what must change."
    >
      <Textarea
        aria-label="Root cause summary"
        value={partC.root_cause_summary}
        onChange={(event) => onPartCChange({ ...partC, root_cause_summary: event.target.value })}
        rows={8}
        data-eid="MOCKUP-NC-WIZ-05:nc_wizard_step3.rca_input"
      />
      <p className={cn('text-xs', rootCauseLength >= 50 ? 'text-success-700' : 'text-neutral-500')}>
        {rootCauseLength}/50 characters
      </p>
    </PromptCard>
  );
}

function PromptCard({ label, hint, children }: { label: string; hint: string; children: ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{label}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-neutral-500">{hint}</p>
        {children}
      </CardContent>
    </Card>
  );
}

function ContextRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase text-neutral-500">{label}</p>
      <p className="mt-1 whitespace-pre-wrap text-neutral-800">{value}</p>
    </div>
  );
}
