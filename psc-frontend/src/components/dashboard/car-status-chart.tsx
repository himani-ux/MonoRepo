/**
 * CAR Status Distribution — Donut/Pie Chart
 */

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Card, CardContent } from '@/components/ui';
import type { CARStatusCount } from '@/lib/api/dashboard';

export interface CARStatusChartProps {
  data: CARStatusCount[];
}

const STATUS_COLORS: Record<string, string> = {
  DRAFT: '#94a3b8',          // slate-400
  SUBMITTED: '#3b82f6',     // blue-500
  PIC_ACCEPTED: '#10b981',  // emerald-500
  REWORK_REQUESTED: '#f59e0b', // amber-500
  DPA_CLOSED: '#6b7280',    // gray-500
};

const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  PIC_ACCEPTED: 'PIC Accepted',
  REWORK_REQUESTED: 'Rework',
  DPA_CLOSED: 'DPA Closed',
};

export function CARStatusChart({ data }: CARStatusChartProps) {
  const chartData = data.map((item) => ({
    name: STATUS_LABELS[item.status] || item.status,
    value: item.count,
    status: item.status,
  }));

  const total = chartData.reduce((sum, d) => sum + d.value, 0);

  if (total === 0) {
    return (
      <Card>
        <CardContent className="p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">CAR Status Distribution</h3>
          <div className="flex items-center justify-center h-48 text-sm text-gray-400">
            No CAR data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">CAR Status Distribution</h3>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((entry) => (
                <Cell
                  key={entry.status}
                  fill={STATUS_COLORS[entry.status] || '#94a3b8'}
                />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => [value ?? 0, 'Count']}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              iconSize={8}
              formatter={(value: string) => (
                <span className="text-xs text-gray-600">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
