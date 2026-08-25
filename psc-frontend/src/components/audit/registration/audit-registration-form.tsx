import { useEffect, useMemo, type FC } from 'react';
import { Controller, useFieldArray, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Plus, Trash2 } from 'lucide-react';
import {
  AUDIT_STANDARDS,
  AUDIT_TEAM_ROLES,
  OFFICE_DEPARTMENTS,
  auditRegistrationDefaults,
  auditRegistrationSchema,
  type AuditRegistrationFormData,
} from '@/schemas/audit/registration';
import { Button, Checkbox, Input, Label, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Textarea } from '@/components/ui';

export interface AuditVesselOption {
  id: string;
  label?: string;
  vessel_code?: string;
  vessel_name?: string;
}

export interface AuditRegistrationPlanOption {
  id: string;
  target_vessel_id: string | null;
  target_office_dept: string | null;
  target_label: string;
  audit_standards_csv: string;
  lead_auditor_user_id: string | null;
  lead_auditor_name?: string | null;
  lead_auditor_designation?: string | null;
  lead_auditor_company?: string | null;
  lead_auditor_qual?: string | null;
  planned_window_start: string | null;
  planned_window_end: string | null;
  window_label: string;
  extended_due_date: string | null;
  extension_form_ref: string | null;
  is_additional: boolean;
  additional_reason: string | null;
  trigger_event_type: string | null;
  trigger_event_ref: string | null;
  status: string;
}

export interface AuditRegistrationFormProps {
  onSubmit: (data: AuditRegistrationFormData) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
  vesselOptions?: AuditVesselOption[];
  auditPlanOptions?: AuditRegistrationPlanOption[];
  defaultVesselId?: string | null;
  defaultLeadAuditorName?: string;
}

const sectionTitleClass = 'text-lg font-semibold text-neutral-900';
const gridClass = 'grid gap-4 md:grid-cols-2';

export const AuditRegistrationForm: FC<AuditRegistrationFormProps> = ({
  onSubmit,
  onCancel,
  isSubmitting = false,
  vesselOptions = [],
  auditPlanOptions = [],
  defaultVesselId,
  defaultLeadAuditorName,
}) => {
  const {
    control,
    register,
    handleSubmit,
    watch,
    setValue,
    setError,
    clearErrors,
    formState: { errors },
  } = useForm<AuditRegistrationFormData>({
    resolver: zodResolver(auditRegistrationSchema),
    defaultValues: {
      ...auditRegistrationDefaults,
      vessel_id: defaultVesselId || vesselOptions[0]?.id || '',
      lead_auditor_name: defaultLeadAuditorName || '',
      inspector_name: defaultLeadAuditorName || '',
    },
  });

  const team = useFieldArray({ control, name: 'team_members' });
  const attendees = useFieldArray({ control, name: 'attendees' });
  const schedule = useFieldArray({ control, name: 'schedule_blocks' });
  const auditeeType = watch('auditee_type');
  const standards = watch('standards');
  const selectedVesselId = watch('vessel_id');
  const selectedAuditPlanId = watch('audit_plan_id') || '';
  const requiresAuditPlanSelection = auditPlanOptions.length > 0;
  const selectedAuditPlan = useMemo(
    () => auditPlanOptions.find((plan) => plan.id === selectedAuditPlanId) ?? null,
    [auditPlanOptions, selectedAuditPlanId]
  );
  const lockLeadAuditorFields = Boolean(selectedAuditPlan);

  useEffect(() => {
    if (!selectedVesselId && vesselOptions[0]?.id) {
      setValue('vessel_id', vesselOptions[0].id, { shouldValidate: true });
    }
  }, [selectedVesselId, setValue, vesselOptions]);

  const toggleStandard = (standard: (typeof AUDIT_STANDARDS)[number], checked: boolean) => {
    const next = checked
      ? Array.from(new Set([...standards, standard]))
      : standards.filter((value) => value !== standard);
    setValue('standards', next, { shouldValidate: true });
  };

  const applyAuditPlan = (planId: string) => {
    setValue('audit_plan_id', planId, { shouldValidate: true });
    clearErrors('audit_plan_id');

    const plan = auditPlanOptions.find((item) => item.id === planId);
    if (!plan) {
      return;
    }

    if (plan.target_vessel_id) {
      setValue('auditee_type', 'VESSEL', { shouldValidate: true });
      setValue('vessel_id', plan.target_vessel_id, { shouldValidate: true });
      setValue('auditee_office_dept', '', { shouldValidate: true });
    }
    if (plan.target_office_dept) {
      setValue('auditee_type', 'OFFICE_DEPT', { shouldValidate: true });
      setValue('auditee_office_dept', plan.target_office_dept as AuditRegistrationFormData['auditee_office_dept'], {
        shouldValidate: true,
      });
    }
    if (plan.lead_auditor_user_id) {
      setValue('lead_auditor_user_id', plan.lead_auditor_user_id, { shouldValidate: true });
    }
    setValue('lead_auditor_name', plan.lead_auditor_name || plan.lead_auditor_user_id || '', { shouldValidate: true });
    setValue('lead_auditor_designation', plan.lead_auditor_designation || '', { shouldValidate: true });
    setValue('lead_auditor_company', plan.lead_auditor_company || 'KSM', { shouldValidate: true });
    setValue('lead_auditor_qual', plan.lead_auditor_qual || '', { shouldValidate: true });
    clearErrors(['lead_auditor_name', 'lead_auditor_company']);

    const planStandards = parsePlanStandards(plan.audit_standards_csv);
    if (planStandards.length > 0) {
      setValue('standards', planStandards, { shouldValidate: true });
    }
  };

  const clearAuditPlan = () => {
    setValue('audit_plan_id', '', { shouldValidate: true });
    setValue('lead_auditor_user_id', '', { shouldValidate: true });
    setValue('lead_auditor_name', defaultLeadAuditorName || '', { shouldValidate: true });
    setValue('lead_auditor_designation', '', { shouldValidate: true });
    setValue('lead_auditor_company', 'KSM', { shouldValidate: true });
    setValue('lead_auditor_qual', '', { shouldValidate: true });
  };

  const submitRegistration = (data: AuditRegistrationFormData) => {
    if (requiresAuditPlanSelection && !data.audit_plan_id) {
      setError('audit_plan_id', {
        type: 'manual',
        message: 'Select the exact audit plan before registering.',
      });
      return;
    }
    onSubmit(data);
  };

  return (
    <form className="space-y-6" onSubmit={handleSubmit(submitRegistration)} noValidate>
      <section className="space-y-4 rounded-md border border-neutral-200 bg-white p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="min-w-0 flex-1 space-y-2">
            <Label htmlFor="audit_plan_id">
              Selected Audit Plan
              {requiresAuditPlanSelection && <span className="text-error-500"> *</span>}
            </Label>
            <Controller
              control={control}
              name="audit_plan_id"
              render={({ field }) => (
                <Select
                  value={field.value || undefined}
                  onValueChange={(value) => {
                    field.onChange(value);
                    applyAuditPlan(value);
                  }}
                  disabled={isSubmitting || auditPlanOptions.length === 0}
                >
                  <SelectTrigger id="audit_plan_id" error={!!errors.audit_plan_id}>
                    <SelectValue placeholder={auditPlanOptions.length > 0 ? 'Select audit plan' : 'No registerable plans available'} />
                  </SelectTrigger>
                  <SelectContent>
                    {auditPlanOptions.map((plan) => (
                      <SelectItem key={plan.id} value={plan.id}>
                        {formatAuditPlanOption(plan)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.audit_plan_id && <p className="text-sm text-error-500">{errors.audit_plan_id.message}</p>}
            {!requiresAuditPlanSelection && (
              <p className="text-sm text-neutral-500">
                No registerable audit plans are available. Register only an approved ad-hoc audit from here.
              </p>
            )}
          </div>
          {selectedAuditPlan && (
            <Button type="button" variant="outline" onClick={clearAuditPlan} disabled={isSubmitting}>
              Clear Plan
            </Button>
          )}
        </div>

        {selectedAuditPlan && (
          <dl className="grid gap-3 rounded-md border border-primary-100 bg-primary-50 p-3 text-sm md:grid-cols-3">
            <SummaryItem label="Plan Ref" value={shortAuditPlanRef(selectedAuditPlan.id)} />
            <SummaryItem label="Target" value={selectedAuditPlan.target_label || '-'} />
            <SummaryItem label="Status" value={selectedAuditPlan.status || '-'} />
            <SummaryItem label="Standards" value={selectedAuditPlan.audit_standards_csv || '-'} />
            <SummaryItem label="Window" value={formatAuditPlanWindow(selectedAuditPlan)} />
            <SummaryItem label="OPM F 713" value={selectedAuditPlan.extension_form_ref || '-'} />
            {selectedAuditPlan.is_additional && (
              <SummaryItem label="Additional Reason" value={selectedAuditPlan.additional_reason || '-'} className="md:col-span-3" />
            )}
          </dl>
        )}
      </section>

      <section className="space-y-4">
        <h2 className={sectionTitleClass}>Common Header</h2>
        <div className={gridClass}>
          <div className="space-y-2">
            <Label htmlFor="vessel_id">Vessel <span className="text-error-500">*</span></Label>
            <Controller
              control={control}
              name="vessel_id"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange} disabled={isSubmitting || vesselOptions.length === 0 || Boolean(selectedAuditPlan)}>
                  <SelectTrigger id="vessel_id" error={!!errors.vessel_id}>
                    <SelectValue placeholder={vesselOptions.length > 0 ? 'Select vessel' : 'No vessels available'} />
                  </SelectTrigger>
                  <SelectContent>
                    {vesselOptions.map((vessel) => (
                      <SelectItem key={vessel.id} value={vessel.id}>
                        {formatVesselOption(vessel)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.vessel_id && <p className="text-sm text-error-500">{errors.vessel_id.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="inspection_date">Inspection Date <span className="text-error-500">*</span></Label>
            <Input id="inspection_date" type="date" disabled={isSubmitting} {...register('inspection_date')} />
            {errors.inspection_date && <p className="text-sm text-error-500">{errors.inspection_date.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="port_place">Port/Place <span className="text-error-500">*</span></Label>
            <Input id="port_place" disabled={isSubmitting} {...register('port_place')} />
            {errors.port_place && <p className="text-sm text-error-500">{errors.port_place.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="country">Country</Label>
            <Input id="country" disabled={isSubmitting} {...register('country')} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="inspector_name">Inspector Name</Label>
            <Input id="inspector_name" disabled={isSubmitting} {...register('inspector_name')} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="report_reference">Report Reference</Label>
            <Input id="report_reference" disabled={isSubmitting} {...register('report_reference')} />
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className={sectionTitleClass}>Audit Classification</h2>
        <div className={gridClass}>
          <div className="space-y-2">
            <Label>Classification</Label>
            <Input value="Internal" disabled readOnly />
          </div>

          <div className="space-y-2">
            <Label>Subtype</Label>
            <Input value="Annual Internal" disabled readOnly />
          </div>

          <div className="space-y-2">
            <Label htmlFor="auditee_type">Auditee Type <span className="text-error-500">*</span></Label>
            <Controller
              control={control}
              name="auditee_type"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange} disabled={isSubmitting || Boolean(selectedAuditPlan)}>
                  <SelectTrigger id="auditee_type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="VESSEL">Vessel</SelectItem>
                    <SelectItem value="OFFICE_DEPT">Office Department</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          {auditeeType === 'OFFICE_DEPT' && (
            <div className="space-y-2">
              <Label htmlFor="auditee_office_dept">Office Department <span className="text-error-500">*</span></Label>
              <Controller
                control={control}
                name="auditee_office_dept"
                render={({ field }) => (
                  <Select value={field.value || ''} onValueChange={field.onChange} disabled={isSubmitting || Boolean(selectedAuditPlan)}>
                    <SelectTrigger id="auditee_office_dept" error={!!errors.auditee_office_dept}>
                      <SelectValue placeholder="Select department" />
                    </SelectTrigger>
                    <SelectContent>
                      {OFFICE_DEPARTMENTS.map((department) => (
                        <SelectItem key={department} value={department}>
                          {department}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
              {errors.auditee_office_dept && <p className="text-sm text-error-500">{errors.auditee_office_dept.message}</p>}
            </div>
          )}
        </div>

        <div className="space-y-2">
          <Label>Harmonised Standards <span className="text-error-500">*</span></Label>
          <div className="grid gap-3 sm:grid-cols-4">
            {AUDIT_STANDARDS.map((standard) => (
              <label key={standard} className="flex items-center gap-2 rounded-md border border-neutral-200 px-3 py-2 text-sm text-neutral-700">
                <Checkbox
                  checked={standards.includes(standard)}
                  onCheckedChange={(checked) => toggleStandard(standard, Boolean(checked))}
                  disabled={isSubmitting || Boolean(selectedAuditPlan)}
                />
                {standard}
              </label>
            ))}
          </div>
          {errors.standards && <p className="text-sm text-error-500">{errors.standards.message}</p>}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className={sectionTitleClass}>Lead Auditor</h2>
        <div className={gridClass}>
          <div className="space-y-2">
            <Label htmlFor="lead_auditor_name">Name <span className="text-error-500">*</span></Label>
            <Input id="lead_auditor_name" readOnly={lockLeadAuditorFields} disabled={isSubmitting} {...register('lead_auditor_name')} />
            {errors.lead_auditor_name && <p className="text-sm text-error-500">{errors.lead_auditor_name.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="lead_auditor_designation">Designation</Label>
            <Input id="lead_auditor_designation" readOnly={lockLeadAuditorFields} disabled={isSubmitting} {...register('lead_auditor_designation')} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="lead_auditor_company">Company <span className="text-error-500">*</span></Label>
            <Input id="lead_auditor_company" readOnly={lockLeadAuditorFields} disabled={isSubmitting} {...register('lead_auditor_company')} />
            {errors.lead_auditor_company && <p className="text-sm text-error-500">{errors.lead_auditor_company.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="lead_auditor_qual">Qualification</Label>
            <Input id="lead_auditor_qual" readOnly={lockLeadAuditorFields} disabled={isSubmitting} {...register('lead_auditor_qual')} />
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className={sectionTitleClass}>Audit Team</h2>
          <Button
            type="button"
            variant="outline"
            onClick={() => team.append({ member_name: '', member_designation: '', member_company: 'KSM', member_role: 'CO_AUDITOR' })}
            disabled={isSubmitting}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add
          </Button>
        </div>
        <div className="space-y-3">
          {team.fields.map((field, index) => (
            <div key={field.id} className="grid gap-3 rounded-md border border-neutral-200 p-3 md:grid-cols-[1fr_1fr_1fr_180px_auto]">
              <Input aria-label="Team member name" placeholder="Name" disabled={isSubmitting} {...register(`team_members.${index}.member_name`)} />
              <Input aria-label="Team designation" placeholder="Designation" disabled={isSubmitting} {...register(`team_members.${index}.member_designation`)} />
              <Input aria-label="Team company" placeholder="Company" disabled={isSubmitting} {...register(`team_members.${index}.member_company`)} />
              <Controller
                control={control}
                name={`team_members.${index}.member_role`}
                render={({ field: roleField }) => (
                  <Select value={roleField.value || ''} onValueChange={roleField.onChange} disabled={isSubmitting}>
                    <SelectTrigger aria-label="Team role">
                      <SelectValue placeholder="Role" />
                    </SelectTrigger>
                    <SelectContent>
                      {AUDIT_TEAM_ROLES.map((role) => (
                        <SelectItem key={role} value={role}>
                          {role}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
              <Button type="button" variant="outline" onClick={() => team.remove(index)} disabled={isSubmitting} aria-label="Remove team member">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className={sectionTitleClass}>Personnel Present</h2>
          <Button
            type="button"
            variant="outline"
            onClick={() => attendees.append({ attendee_name: '', attendee_rank: '', opening_present: true, closing_present: false })}
            disabled={isSubmitting}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add
          </Button>
        </div>
        <div className="space-y-3">
          {attendees.fields.map((field, index) => (
            <div key={field.id} className="grid gap-3 rounded-md border border-neutral-200 p-3 md:grid-cols-[1fr_1fr_160px_160px_auto]">
              <Input aria-label="Attendee name" placeholder="Name" disabled={isSubmitting} {...register(`attendees.${index}.attendee_name`)} />
              <Input aria-label="Attendee rank" placeholder="Rank" disabled={isSubmitting} {...register(`attendees.${index}.attendee_rank`)} />
              <label className="flex items-center gap-2 text-sm text-neutral-700">
                <Controller control={control} name={`attendees.${index}.opening_present`} render={({ field: presentField }) => (
                  <Checkbox checked={presentField.value} onCheckedChange={presentField.onChange} disabled={isSubmitting} />
                )} />
                Opening
              </label>
              <label className="flex items-center gap-2 text-sm text-neutral-700">
                <Controller control={control} name={`attendees.${index}.closing_present`} render={({ field: presentField }) => (
                  <Checkbox checked={presentField.value} onCheckedChange={presentField.onChange} disabled={isSubmitting} />
                )} />
                Closing
              </label>
              <Button type="button" variant="outline" onClick={() => attendees.remove(index)} disabled={isSubmitting} aria-label="Remove attendee">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className={sectionTitleClass}>Audit Dates & Scope</h2>
        <div className={gridClass}>
          <div className="space-y-2">
            <Label htmlFor="audit_start_date">Audit Start <span className="text-error-500">*</span></Label>
            <Input id="audit_start_date" type="date" disabled={isSubmitting} {...register('audit_start_date')} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="audit_end_date">Audit End</Label>
            <Input id="audit_end_date" type="date" disabled={isSubmitting} {...register('audit_end_date')} />
            {errors.audit_end_date && <p className="text-sm text-error-500">{errors.audit_end_date.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="opening_meeting_at">Opening Meeting</Label>
            <Input id="opening_meeting_at" type="datetime-local" disabled={isSubmitting} {...register('opening_meeting_at')} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="closing_meeting_at">Closing Meeting</Label>
            <Input id="closing_meeting_at" type="datetime-local" disabled={isSubmitting} {...register('closing_meeting_at')} />
          </div>
        </div>
        <div className={gridClass}>
          <div className="space-y-2">
            <Label htmlFor="audit_scope">Audit Scope</Label>
            <Textarea id="audit_scope" rows={4} disabled={isSubmitting} {...register('audit_scope')} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="terms_of_reference">Terms of Reference</Label>
            <Textarea id="terms_of_reference" rows={4} disabled={isSubmitting} {...register('terms_of_reference')} />
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className={sectionTitleClass}>Audit Plan Blocks</h2>
          <Button
            type="button"
            variant="outline"
            onClick={() => schedule.append({ block_date: '', time_from: '', time_to: '', activity: '' })}
            disabled={isSubmitting}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add
          </Button>
        </div>
        <div className="space-y-3">
          {schedule.fields.map((field, index) => (
            <div key={field.id} className="grid gap-3 rounded-md border border-neutral-200 p-3 md:grid-cols-[170px_130px_130px_1fr_auto]">
              <Input aria-label="Schedule date" type="date" disabled={isSubmitting} {...register(`schedule_blocks.${index}.block_date`)} />
              <Input aria-label="Schedule from" type="time" disabled={isSubmitting} {...register(`schedule_blocks.${index}.time_from`)} />
              <Input aria-label="Schedule to" type="time" disabled={isSubmitting} {...register(`schedule_blocks.${index}.time_to`)} />
              <Input aria-label="Schedule activity" placeholder="Activity" disabled={isSubmitting} {...register(`schedule_blocks.${index}.activity`)} />
              <Button type="button" variant="outline" onClick={() => schedule.remove(index)} disabled={isSubmitting} aria-label="Remove schedule block">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </section>

      <div className="flex flex-col-reverse gap-3 border-t border-neutral-200 pt-6 sm:flex-row sm:justify-end">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            'Register Audit'
          )}
        </Button>
      </div>
    </form>
  );
};

function formatVesselOption(vessel: AuditVesselOption): string {
  if (vessel.label) {
    return vessel.label;
  }
  if (vessel.vessel_code && vessel.vessel_name) {
    return `${vessel.vessel_code} - ${vessel.vessel_name}`;
  }
  return vessel.vessel_name || vessel.vessel_code || vessel.id;
}

function SummaryItem({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div className={className}>
      <dt className="text-xs font-semibold uppercase text-primary-700">{label}</dt>
      <dd className="mt-1 break-words text-neutral-800">{value}</dd>
    </div>
  );
}

export function shortAuditPlanRef(id: string): string {
  return `PLAN-${id.slice(0, 8).toUpperCase()}`;
}

export function parsePlanStandards(csv: string): (typeof AUDIT_STANDARDS)[number][] {
  const allowed = new Set<string>(AUDIT_STANDARDS);
  return csv
    .split(',')
    .map((value) => value.trim())
    .filter((value): value is (typeof AUDIT_STANDARDS)[number] => allowed.has(value));
}

export function formatAuditPlanWindow(plan: AuditRegistrationPlanOption): string {
  if (plan.window_label) {
    return plan.window_label;
  }
  if (plan.planned_window_start && plan.planned_window_end) {
    return `${plan.planned_window_start} -> ${plan.planned_window_end}`;
  }
  if (plan.extended_due_date) {
    return `Extended due ${plan.extended_due_date}`;
  }
  return '-';
}

export function formatAuditPlanOption(plan: AuditRegistrationPlanOption): string {
  const parts = [
    shortAuditPlanRef(plan.id),
    plan.target_label || 'Target not set',
    plan.audit_standards_csv || 'Standards not set',
    formatAuditPlanWindow(plan),
    plan.status || 'Status not set',
  ];
  if (plan.is_additional) {
    parts.push('Additional');
  }
  return parts.join(' | ');
}
