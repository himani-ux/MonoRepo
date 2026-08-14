import { useCallback, useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '@/components/layout/page-header';
import { RootLayout } from '@/components/layout/root-layout';
import { Button, Checkbox, Input, Label, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Textarea } from '@/components/ui';
import { useCreateAuditRegistration } from '@/hooks/audit/use-audit-registration';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/api/client';
import {
  EXTERNAL_AUDIT_ORG_TYPES,
  EXTERNAL_AUDIT_STANDARDS,
  EXTERNAL_AUDIT_SUBTYPES,
  externalAuditRegistrationSchema,
  type ExternalAuditRegistrationFormData,
} from '@/schemas/audit/registration';

const today = new Date().toISOString().slice(0, 10);
const sectionTitleClass = 'text-lg font-semibold text-neutral-900';
const gridClass = 'grid gap-4 md:grid-cols-2';

function optionalPositiveNumber(value: unknown): number | null {
  if (value === '' || value === null || value === undefined) {
    return null;
  }
  const parsed = Number(value);
  return Number.isNaN(parsed) ? null : parsed;
}

const defaults: ExternalAuditRegistrationFormData = {
  vessel_id: '',
  inspection_date: today,
  port_place: '',
  country: '',
  authority: '',
  inspector_name: '',
  report_reference: '',
  audit_classification: 'EXTERNAL',
  auditee_type: 'VESSEL',
  auditee_office_dept: '',
  audit_start_date: today,
  audit_end_date: today,
  standards: ['ISM'],
  external_audit_subtypes: ['SMC_RENEWAL'],
  external_audit_org_id: '',
  external_audit_org_type: 'CLASS_SOCIETY',
  external_lead_auditor_name: '',
  external_lead_auditor_credential: '',
  flag_state_code: '',
  cycle_year: null,
  linked_cert_ids: [],
  external_report_file_name: '',
  external_report_file_path: '',
  external_report_mime_type: 'application/pdf',
  external_report_file_size: null,
  late_registration_reason: '',
};

function parseUuidList(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

export function ExternalAuditRegistrationPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const mutation = useCreateAuditRegistration();
  const [linkedCertText, setLinkedCertText] = useState('');
  const {
    control,
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ExternalAuditRegistrationFormData>({
    resolver: zodResolver(externalAuditRegistrationSchema),
    defaultValues: defaults,
  });

  const standards = watch('standards');
  const subtypes = watch('external_audit_subtypes');
  const hasDocSubtype = subtypes.some((subtype) => subtype.startsWith('DOC_'));

  const toggleStandard = (standard: (typeof EXTERNAL_AUDIT_STANDARDS)[number], checked: boolean) => {
    const next = checked
      ? Array.from(new Set([...standards, standard]))
      : standards.filter((value) => value !== standard);
    setValue('standards', next, { shouldValidate: true });
  };

  const toggleSubtype = (subtype: (typeof EXTERNAL_AUDIT_SUBTYPES)[number], checked: boolean) => {
    const next = checked
      ? Array.from(new Set([...subtypes, subtype]))
      : subtypes.filter((value) => value !== subtype);
    setValue('external_audit_subtypes', next, { shouldValidate: true });
  };

  const onSubmit = useCallback(
    async (data: ExternalAuditRegistrationFormData) => {
      try {
        const created = await mutation.mutateAsync({
          ...data,
          linked_cert_ids: parseUuidList(linkedCertText),
        });
        toast({
          title: 'External audit registered',
          description: 'The audit was created at SUBMITTED status.',
        });
        navigate(`/audit/external/${created.id}`);
      } catch (error) {
        toast({
          title: 'Failed to register external audit',
          description: getErrorMessage(error),
          variant: 'destructive',
        });
      }
    },
    [linkedCertText, mutation, navigate, toast]
  );

  return (
    <RootLayout>
      <PageHeader title="External Audit" showBack backTo="/audit/plans" />

      <form className="mx-auto max-w-5xl space-y-6 pb-8" onSubmit={handleSubmit(onSubmit)} noValidate>
        <input type="hidden" {...register('audit_classification')} />
        <input type="hidden" {...register('auditee_type')} />
        <input type="hidden" {...register('external_report_mime_type')} />
        <section className="space-y-4">
          <h2 className={sectionTitleClass}>Post-Facto Registration</h2>
          <div className={gridClass}>
            <div className="space-y-2">
              <Label htmlFor="vessel_id">Vessel UUID <span className="text-error-500">*</span></Label>
              <Input id="vessel_id" disabled={mutation.isPending} {...register('vessel_id')} />
              {errors.vessel_id && <p className="text-sm text-error-500">{errors.vessel_id.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="inspection_date">Completion Date <span className="text-error-500">*</span></Label>
              <Input id="inspection_date" type="date" disabled={mutation.isPending} {...register('inspection_date')} />
              {errors.inspection_date && <p className="text-sm text-error-500">{errors.inspection_date.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="port_place">Port/Place <span className="text-error-500">*</span></Label>
              <Input id="port_place" disabled={mutation.isPending} {...register('port_place')} />
              {errors.port_place && <p className="text-sm text-error-500">{errors.port_place.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="report_reference">Report Reference <span className="text-error-500">*</span></Label>
              <Input id="report_reference" disabled={mutation.isPending} {...register('report_reference')} />
              {errors.report_reference && <p className="text-sm text-error-500">{errors.report_reference.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="audit_start_date">Audit Start <span className="text-error-500">*</span></Label>
              <Input id="audit_start_date" type="date" disabled={mutation.isPending} {...register('audit_start_date')} />
              {errors.audit_start_date && <p className="text-sm text-error-500">{errors.audit_start_date.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="audit_end_date">Audit End</Label>
              <Input id="audit_end_date" type="date" disabled={mutation.isPending} {...register('audit_end_date')} />
              {errors.audit_end_date && <p className="text-sm text-error-500">{errors.audit_end_date.message}</p>}
            </div>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className={sectionTitleClass}>External Audit Definition</h2>
          <div className="space-y-2">
            <Label>Subtypes <span className="text-error-500">*</span></Label>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {EXTERNAL_AUDIT_SUBTYPES.map((subtype) => (
                <label key={subtype} className="flex min-h-10 items-center gap-2 rounded-md border border-neutral-200 px-3 py-2 text-sm text-neutral-700">
                  <Checkbox
                    checked={subtypes.includes(subtype)}
                    onCheckedChange={(checked) => toggleSubtype(subtype, Boolean(checked))}
                    disabled={mutation.isPending}
                  />
                  {subtype}
                </label>
              ))}
            </div>
            {errors.external_audit_subtypes && <p className="text-sm text-error-500">{errors.external_audit_subtypes.message}</p>}
          </div>

          <div className="space-y-2">
            <Label>Standards <span className="text-error-500">*</span></Label>
            <div className="grid gap-2 sm:grid-cols-5">
              {EXTERNAL_AUDIT_STANDARDS.map((standard) => (
                <label key={standard} className="flex min-h-10 items-center gap-2 rounded-md border border-neutral-200 px-3 py-2 text-sm text-neutral-700">
                  <Checkbox
                    checked={standards.includes(standard)}
                    onCheckedChange={(checked) => toggleStandard(standard, Boolean(checked))}
                    disabled={mutation.isPending}
                  />
                  {standard}
                </label>
              ))}
            </div>
          </div>

          <div className={gridClass}>
            <div className="space-y-2">
              <Label htmlFor="external_audit_org_id">External Audit Org UUID <span className="text-error-500">*</span></Label>
              <Input id="external_audit_org_id" disabled={mutation.isPending} {...register('external_audit_org_id')} />
              {errors.external_audit_org_id && <p className="text-sm text-error-500">{errors.external_audit_org_id.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="external_audit_org_type">Org Type <span className="text-error-500">*</span></Label>
              <Controller
                control={control}
                name="external_audit_org_type"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange} disabled={mutation.isPending}>
                    <SelectTrigger id="external_audit_org_type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {EXTERNAL_AUDIT_ORG_TYPES.map((type) => (
                        <SelectItem key={type} value={type}>
                          {type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="external_lead_auditor_name">External Lead Auditor <span className="text-error-500">*</span></Label>
              <Input id="external_lead_auditor_name" disabled={mutation.isPending} {...register('external_lead_auditor_name')} />
              {errors.external_lead_auditor_name && <p className="text-sm text-error-500">{errors.external_lead_auditor_name.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="external_lead_auditor_credential">Auditor Credential <span className="text-error-500">*</span></Label>
              <Input id="external_lead_auditor_credential" disabled={mutation.isPending} {...register('external_lead_auditor_credential')} />
              {errors.external_lead_auditor_credential && <p className="text-sm text-error-500">{errors.external_lead_auditor_credential.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="flag_state_code">Flag State {hasDocSubtype && <span className="text-error-500">*</span>}</Label>
              <Input id="flag_state_code" disabled={mutation.isPending} {...register('flag_state_code')} />
              {errors.flag_state_code && <p className="text-sm text-error-500">{errors.flag_state_code.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="cycle_year">DOC Cycle Year {hasDocSubtype && <span className="text-error-500">*</span>}</Label>
              <Input
                id="cycle_year"
                type="number"
                disabled={mutation.isPending}
                {...register('cycle_year', { setValueAs: optionalPositiveNumber })}
              />
            </div>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className={sectionTitleClass}>Certs Link And Report</h2>
          <div className={gridClass}>
            <div className="space-y-2">
              <Label htmlFor="linked_cert_ids">Linked Certificate UUIDs</Label>
              <Input
                id="linked_cert_ids"
                value={linkedCertText}
                onChange={(event) => setLinkedCertText(event.target.value)}
                disabled={mutation.isPending}
                placeholder="comma-separated certificate ids"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="external_report_file_name">External Audit Report PDF <span className="text-error-500">*</span></Label>
              <Input id="external_report_file_name" disabled={mutation.isPending} {...register('external_report_file_name')} />
              {errors.external_report_file_name && <p className="text-sm text-error-500">{errors.external_report_file_name.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="external_report_file_path">Report File Path <span className="text-error-500">*</span></Label>
              <Input id="external_report_file_path" disabled={mutation.isPending} {...register('external_report_file_path')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="external_report_file_size">Report File Size</Label>
              <Input
                id="external_report_file_size"
                type="number"
                disabled={mutation.isPending}
                {...register('external_report_file_size', { setValueAs: optionalPositiveNumber })}
              />
            </div>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className={sectionTitleClass}>Late Registration</h2>
          <Textarea
            rows={3}
            disabled={mutation.isPending}
            placeholder="DPA override reason, required when registering more than 30 days after completion."
            {...register('late_registration_reason')}
          />
          {errors.late_registration_reason && <p className="text-sm text-error-500">{errors.late_registration_reason.message}</p>}
        </section>

        <div className="flex flex-col-reverse gap-3 border-t border-neutral-200 pt-6 sm:flex-row sm:justify-end">
          <Button type="button" variant="outline" onClick={() => navigate('/audit/plans')} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Registering...
              </>
            ) : (
              'Register External Audit'
            )}
          </Button>
        </div>
      </form>
    </RootLayout>
  );
}
