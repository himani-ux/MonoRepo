import { useMemo, useState, type FormEvent } from 'react';
import { Loader2, Pencil, Plus, RotateCcw, Save, UserCheck } from 'lucide-react';
import { PageHeader } from '@/components/layout/page-header';
import { RootLayout } from '@/components/layout/root-layout';
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Checkbox,
  Input,
  Label,
} from '@/components/ui';
import {
  useAuditOfficeUsers,
  useAuditQualifyingBodies,
  useAuditQualifiedAuditorMaster,
  useCreateAuditQualifiedAuditor,
  useUpdateAuditQualifiedAuditor,
} from '@/hooks/audit/use-audit-plan';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/api/client';
import type { AuditOfficeUserOption, AuditQualifiedAuditor } from '@/lib/api/audit';

const standardOptions = ['ISM', 'ISPS', 'MLC', 'EMS'] as const;
const auditorScopes = ['OFFICE_SIDE', 'VESSEL_SIDE'] as const;

interface QualifiedAuditorFormState {
  id: string | null;
  user_id: string;
  qualification_text: string;
  qualification_date: string;
  expiry_date: string;
  scope_standards_csv: string;
  qualifying_body: string;
  certificate_attachment_id: string;
  auditor_scope: string;
  qualified_for_seq: boolean;
  is_active: boolean;
}

const emptyForm: QualifiedAuditorFormState = {
  id: null,
  user_id: '',
  qualification_text: '',
  qualification_date: new Date().toISOString().slice(0, 10),
  expiry_date: '',
  scope_standards_csv: 'ISM',
  qualifying_body: '',
  certificate_attachment_id: '',
  auditor_scope: 'OFFICE_SIDE',
  qualified_for_seq: false,
  is_active: true,
};

function parseStandards(value: string) {
  return value
    .split(',')
    .map((part) => part.trim().toUpperCase())
    .filter(Boolean);
}

function normalizeStandards(standards: string[]) {
  return standardOptions.filter((standard) => standards.includes(standard)).join(',');
}

function toForm(row: AuditQualifiedAuditor): QualifiedAuditorFormState {
  return {
    id: row.id,
    user_id: row.user_id,
    qualification_text: row.qualification_text,
    qualification_date: row.qualification_date,
    expiry_date: row.expiry_date,
    scope_standards_csv: row.scope_standards_csv,
    qualifying_body: row.qualifying_body ?? '',
    certificate_attachment_id: row.certificate_attachment_id ?? '',
    auditor_scope: row.auditor_scope || 'OFFICE_SIDE',
    qualified_for_seq: row.qualified_for_seq,
    is_active: row.is_active,
  };
}

function formatOfficeUserOption(user: AuditOfficeUserOption): string {
  const name = user.display_name || user.employee_name || user.username || user.employee_id;
  const role = user.role_name || 'Role not set';
  return `${name} - ${role}`;
}

export default function AuditQualifiedAuditorsRoute() {
  const { toast } = useToast();
  const qualifiedAuditors = useAuditQualifiedAuditorMaster();
  const officeUsers = useAuditOfficeUsers();
  const qualifyingBodies = useAuditQualifyingBodies();
  const createAuditor = useCreateAuditQualifiedAuditor();
  const updateAuditor = useUpdateAuditQualifiedAuditor();
  const [form, setForm] = useState<QualifiedAuditorFormState>(emptyForm);
  const selectedStandards = parseStandards(form.scope_standards_csv);
  const rows = useMemo(
    () => [...(qualifiedAuditors.data?.results ?? [])].sort((a, b) => Number(b.is_active) - Number(a.is_active)),
    [qualifiedAuditors.data?.results]
  );
  const officeUserOptions = officeUsers.data?.results ?? [];
  const qualifyingBodyOptions = qualifyingBodies.data?.results ?? [];
  const currentUserIsListed = officeUserOptions.some((user) => user.employee_id === form.user_id);
  const currentQualifyingBodyIsListed =
    !form.qualifying_body || qualifyingBodyOptions.some((body) => body.body_name === form.qualifying_body);
  const isSaving = createAuditor.isPending || updateAuditor.isPending;
  const canSave = Boolean(
    form.user_id.trim() &&
    form.qualification_text.trim() &&
    form.qualification_date &&
    form.expiry_date &&
    selectedStandards.length
  );

  const setField = <TKey extends keyof QualifiedAuditorFormState>(
    key: TKey,
    value: QualifiedAuditorFormState[TKey]
  ) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const setStandard = (standard: string, checked: boolean) => {
    const next = checked
      ? [...selectedStandards, standard]
      : selectedStandards.filter((value) => value !== standard);
    setField('scope_standards_csv', normalizeStandards(next));
  };

  const resetForm = () => {
    setForm(emptyForm);
  };

  const saveAuditor = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const payload = {
      user_id: form.user_id.trim(),
      qualification_text: form.qualification_text.trim(),
      qualification_date: form.qualification_date,
      expiry_date: form.expiry_date,
      scope_standards_csv: normalizeStandards(selectedStandards),
      qualifying_body: form.qualifying_body.trim() || null,
      certificate_attachment_id: form.certificate_attachment_id.trim() || null,
      auditor_scope: form.auditor_scope,
      qualified_for_seq: form.qualified_for_seq,
      is_active: form.is_active,
    };

    try {
      if (form.id) {
        await updateAuditor.mutateAsync({ id: form.id, data: payload });
        toast({ title: 'Qualified auditor updated' });
      } else {
        await createAuditor.mutateAsync(payload);
        toast({ title: 'Qualified auditor added' });
      }
      resetForm();
    } catch (error) {
      toast({
        title: form.id ? 'Qualified auditor not updated' : 'Qualified auditor not added',
        description: getErrorMessage(error),
        variant: 'destructive',
      });
    }
  };

  const toggleActive = async (row: AuditQualifiedAuditor) => {
    try {
      await updateAuditor.mutateAsync({ id: row.id, data: { is_active: !row.is_active } });
      toast({ title: row.is_active ? 'Qualified auditor deactivated' : 'Qualified auditor activated' });
    } catch (error) {
      toast({
        title: 'Qualified auditor status not changed',
        description: getErrorMessage(error),
        variant: 'destructive',
      });
    }
  };

  return (
    <RootLayout>
      <PageHeader title="Qualified Auditors" showBack backTo="/audit" />
      <div className="space-y-4 p-4 md:p-6">
        <Card>
          <CardHeader>
            <CardTitle>{form.id ? 'Edit Qualified Auditor' : 'Add Qualified Auditor'}</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4 md:grid-cols-4" onSubmit={saveAuditor}>
              <div className="space-y-2">
                <Label htmlFor="qa_user_id">Employee/User ID</Label>
                <select
                  id="qa_user_id"
                  value={form.user_id}
                  onChange={(event) => setField('user_id', event.target.value)}
                  className="h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                  disabled={officeUsers.isLoading}
                  required
                >
                  <option value="">{officeUsers.isLoading ? 'Loading office users...' : 'Select office user'}</option>
                  {officeUserOptions.map((user) => (
                    <option key={user.employee_id} value={user.employee_id}>
                      {formatOfficeUserOption(user)}
                    </option>
                  ))}
                  {form.user_id && !currentUserIsListed ? (
                    <option value={form.user_id}>{form.user_id} - not in active office users</option>
                  ) : null}
                </select>
                {officeUsers.isError ? (
                  <p className="text-xs text-error-700">{getErrorMessage(officeUsers.error)}</p>
                ) : null}
              </div>
              <div className="space-y-2">
                <Label htmlFor="qa_scope">Auditor Scope</Label>
                <select
                  id="qa_scope"
                  value={form.auditor_scope}
                  onChange={(event) => setField('auditor_scope', event.target.value)}
                  className="h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                >
                  {auditorScopes.map((scope) => (
                    <option key={scope} value={scope}>
                      {scope}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="qa_qualification_date">Qualification Date</Label>
                <Input
                  id="qa_qualification_date"
                  type="date"
                  value={form.qualification_date}
                  onChange={(event) => setField('qualification_date', event.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="qa_expiry_date">Expiry Date</Label>
                <Input
                  id="qa_expiry_date"
                  type="date"
                  value={form.expiry_date}
                  onChange={(event) => setField('expiry_date', event.target.value)}
                  required
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="qa_qualification">Qualification</Label>
                <Input
                  id="qa_qualification"
                  value={form.qualification_text}
                  onChange={(event) => setField('qualification_text', event.target.value)}
                  maxLength={200}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="qa_body">Qualifying Body</Label>
                <select
                  id="qa_body"
                  value={form.qualifying_body}
                  onChange={(event) => setField('qualifying_body', event.target.value)}
                  className="h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                  disabled={qualifyingBodies.isLoading}
                >
                  <option value="">
                    {qualifyingBodies.isLoading ? 'Loading qualifying bodies...' : 'Select qualifying body'}
                  </option>
                  {qualifyingBodyOptions.map((body) => (
                    <option key={body.id} value={body.body_name}>
                      {body.body_name}
                    </option>
                  ))}
                  {form.qualifying_body && !currentQualifyingBodyIsListed ? (
                    <option value={form.qualifying_body}>{form.qualifying_body}</option>
                  ) : null}
                </select>
                {qualifyingBodies.isError ? (
                  <p className="text-xs text-error-700">{getErrorMessage(qualifyingBodies.error)}</p>
                ) : null}
              </div>
              <fieldset className="space-y-2 md:col-span-2">
                <legend className="text-sm font-medium text-neutral-800">Standards</legend>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {standardOptions.map((standard) => (
                    <label
                      key={standard}
                      className="flex h-10 items-center gap-2 rounded-md border border-neutral-200 px-3 text-sm text-neutral-700"
                    >
                      <Checkbox
                        checked={selectedStandards.includes(standard)}
                        onCheckedChange={(checked) => setStandard(standard, Boolean(checked))}
                      />
                      {standard}
                    </label>
                  ))}
                </div>
              </fieldset>
              <div className="flex items-end gap-4">
                <label className="flex h-10 items-center gap-2 text-sm text-neutral-700">
                  <Checkbox
                    checked={form.qualified_for_seq}
                    onCheckedChange={(checked) => setField('qualified_for_seq', Boolean(checked))}
                  />
                  SEQ qualified
                </label>
                <label className="flex h-10 items-center gap-2 text-sm text-neutral-700">
                  <Checkbox
                    checked={form.is_active}
                    onCheckedChange={(checked) => setField('is_active', Boolean(checked))}
                  />
                  Active
                </label>
              </div>
              <div className="flex items-end justify-end gap-2">
                <Button type="button" variant="outline" onClick={resetForm}>
                  <RotateCcw className="mr-2 h-4 w-4" />
                  Reset
                </Button>
                <Button type="submit" disabled={!canSave || isSaving}>
                  {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                  Save
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Qualified Auditor Master</CardTitle>
          </CardHeader>
          <CardContent>
            {qualifiedAuditors.isLoading ? (
              <div className="flex items-center gap-2 text-sm text-neutral-600">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading qualified auditors
              </div>
            ) : qualifiedAuditors.isError ? (
              <div className="rounded-md border border-error-200 bg-error-50 p-3 text-sm text-error-700">
                {getErrorMessage(qualifiedAuditors.error)}
              </div>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-neutral-200">
                <table className="min-w-full divide-y divide-neutral-200 text-sm">
                  <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                    <tr>
                      <th className="px-3 py-2">Auditor</th>
                      <th className="px-3 py-2">Qualification</th>
                      <th className="px-3 py-2">Standards</th>
                      <th className="px-3 py-2">Expiry</th>
                      <th className="px-3 py-2">Status</th>
                      <th className="px-3 py-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100 bg-white">
                    {rows.map((row) => (
                      <tr key={row.id}>
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-2 font-medium text-neutral-900">
                            <UserCheck className="h-4 w-4 text-primary-600" />
                            {row.display_name || row.user_id}
                          </div>
                          <div className="mt-1 text-xs text-neutral-500">
                            {row.user_id} - {row.designation || row.auditor_scope} - {row.company || row.identity_source}
                          </div>
                        </td>
                        <td className="px-3 py-2">
                          <div>{row.qualification_text}</div>
                          <div className="mt-1 text-xs text-neutral-500">{row.qualifying_body || 'Body not set'}</div>
                        </td>
                        <td className="px-3 py-2 font-mono text-xs">{row.scope_standards_csv}</td>
                        <td className="px-3 py-2 font-mono text-xs">{row.expiry_date}</td>
                        <td className="px-3 py-2">
                          <Badge variant={row.is_active ? 'success' : 'secondary'}>
                            {row.is_active ? 'ACTIVE' : 'INACTIVE'}
                          </Badge>
                          {row.qualified_for_seq ? <Badge className="ml-2" variant="info">SEQ</Badge> : null}
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex flex-wrap gap-2">
                            <Button type="button" variant="outline" size="sm" onClick={() => setForm(toForm(row))}>
                              <Pencil className="mr-2 h-4 w-4" />
                              Edit
                            </Button>
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => toggleActive(row)}
                              disabled={updateAuditor.isPending}
                            >
                              {row.is_active ? 'Deactivate' : 'Activate'}
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {!rows.length ? (
                      <tr>
                        <td className="px-3 py-6 text-center text-neutral-500" colSpan={6}>
                          No qualified auditors found.
                        </td>
                      </tr>
                    ) : null}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </RootLayout>
  );
}
