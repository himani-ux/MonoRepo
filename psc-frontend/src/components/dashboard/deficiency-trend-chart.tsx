/**
 * Monthly Deficiency Trend — Bar Chart (12 months)
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent } from '@/components/ui';
import type { MonthlyDefTrend } from '@/lib/api/dashboard';

export interface DeficiencyTrendChartProps {
  data: MonthlyDefTrend[];
}

function formatMonth(month: string): string {
  // "2025-06" → "Jun 25"
  const [year, m] = month.split('-');
  const date = new Date(Number(year), Number(m) - 1);
  return date.toLocaleDateString('en-GB', { month: 'short', year: '2-digit' });
}

export function DeficiencyTrendChart({ data }: DeficiencyTrendChartProps) {
  const chartData = data.map((item) => ({
    month: formatMonth(item.month),
    count: item.count,
  }));

  if (chartData.length === 0) {
    return (
      <Card>
        <CardContent className="p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Monthly Deficiency Trend</h3>
          <div className="flex items-center justify-center h-48 text-sm text-gray-400">
            No deficiency data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Monthly Deficiency Trend</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 11 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              width={30}
            />
            <Tooltip
              formatter={(value) => [value ?? 0, 'Deficiencies']}
            />
            <Bar
              dataKey="count"
              fill="#3b82f6"
              radius={[4, 4, 0, 0]}
              maxBarSize={40}
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
