import { useState } from 'react';
import { Loader2, Plus, XCircle } from 'lucide-react';
import { PageHeader } from '@/components/layout/page-header';
import { RootLayout } from '@/components/layout/root-layout';
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label } from '@/components/ui';
import {
  useAuditHodCoverage,
  useCreateAuditHodAssignment,
  useExpireAuditHodAssignment,
} from '@/hooks/audit/use-audit-plan';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/api/client';

const departments = ['CREW', 'TECH', 'PURCHASE', 'IT', 'MARINE', 'SEQ', 'OTHER'];

const emptyForm = {
  dept: 'CREW',
  user_id: '',
  effective_from: new Date().toISOString().slice(0, 10),
  effective_to: '',
};

export default function HodCoverageRoute() {
  const { toast } = useToast();
  const coverage = useAuditHodCoverage();
  const createAssignment = useCreateAuditHodAssignment();
  const expireAssignment = useExpireAuditHodAssignment();
  const [form, setForm] = useState(emptyForm);

  const saveAssignment = async () => {
    try {
      await createAssignment.mutateAsync(form);
      toast({ title: 'Acting HoD assignment saved' });
      setForm(emptyForm);
    } catch (error) {
      toast({
        title: 'Acting HoD assignment not saved',
        description: getErrorMessage(error),
        variant: 'destructive',
      });
    }
  };

  const closeAssignment = async (id: string) => {
    try {
      await expireAssignment.mutateAsync(id);
      toast({ title: 'Acting HoD assignment closed' });
    } catch (error) {
      toast({
        title: 'Acting HoD assignment not closed',
        description: getErrorMessage(error),
        variant: 'destructive',
      });
    }
  };

  return (
    <RootLayout>
      <PageHeader title="HoD Coverage" showBack backTo="/audit" />
      <div className="space-y-4 p-4">
        <Card>
          <CardHeader>
            <CardTitle>Assign Acting HoD</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <Label htmlFor="hod_dept">Department</Label>
              <select
                id="hod_dept"
                value={form.dept}
                onChange={(event) => setForm((current) => ({ ...current, dept: event.target.value }))}
                className="h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              >
                {departments.map((department) => (
                  <option key={department} value={department}>
                    {department}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="hod_user_id">Employee/User ID</Label>
              <Input
                id="hod_user_id"
                value={form.user_id}
                onChange={(event) => setForm((current) => ({ ...current, user_id: event.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="hod_from">From</Label>
              <Input
                id="hod_from"
                type="date"
                value={form.effective_from}
                onChange={(event) => setForm((current) => ({ ...current, effective_from: event.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="hod_to">To</Label>
              <Input
                id="hod_to"
                type="date"
                value={form.effective_to}
                onChange={(event) => setForm((current) => ({ ...current, effective_to: event.target.value }))}
              />
            </div>
            <div className="md:col-span-4">
              <Button
                type="button"
                onClick={saveAssignment}
                disabled={createAssignment.isPending || !form.user_id || !form.effective_from || !form.effective_to}
              >
                {createAssignment.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                Save assignment
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Active HoD Coverage</CardTitle>
          </CardHeader>
          <CardContent>
            {coverage.isLoading ? (
              <div className="flex items-center gap-2 text-sm text-neutral-600">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading coverage
              </div>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-neutral-200">
                <table className="min-w-full divide-y divide-neutral-200 text-sm">
                  <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                    <tr>
                      <th className="px-3 py-2">Department</th>
                      <th className="px-3 py-2">Acting HoD</th>
                      <th className="px-3 py-2">Window</th>
                      <th className="px-3 py-2">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100 bg-white">
                    {(coverage.data?.results ?? []).map((assignment) => (
                      <tr key={assignment.id}>
                        <td className="px-3 py-2 font-medium">{assignment.dept}</td>
                        <td className="px-3 py-2">
                          <div>{assignment.display_name || assignment.user_id}</div>
                          <div className="text-xs text-neutral-500">{assignment.designation || assignment.user_id}</div>
                        </td>
                        <td className="px-3 py-2 font-mono text-xs">
                          {assignment.effective_from} to {assignment.effective_to || 'open'}
                        </td>
                        <td className="px-3 py-2">
                          {assignment.is_acting ? (
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => closeAssignment(assignment.id)}
                              disabled={expireAssignment.isPending}
                            >
                              <XCircle className="mr-2 h-4 w-4" />
                              Close
                            </Button>
                          ) : (
                            <span className="text-xs text-neutral-500">Primary HoD</span>
                          )}
                        </td>
                      </tr>
                    ))}
                    {!coverage.data?.results.length && (
                      <tr>
                        <td className="px-3 py-6 text-center text-neutral-500" colSpan={4}>
                          No active HoD coverage rows.
                        </td>
                      </tr>
                    )}
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
