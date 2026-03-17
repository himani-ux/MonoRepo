/**
 * Top Deficiency Codes — Horizontal Bar Chart
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
import type { TopDefCode } from '@/lib/api/dashboard';

export interface TopDefCodesProps {
  data: TopDefCode[];
}

export function TopDefCodes({ data }: TopDefCodesProps) {
  const chartData = data.map((item) => ({
    code: item.def_code,
    description: item.def_code_description,
    count: item.count,
  }));

  if (chartData.length === 0) {
    return (
      <Card>
        <CardContent className="p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Top Deficiency Codes</h3>
          <div className="flex items-center justify-center h-48 text-sm text-gray-400">
            No deficiency code data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Top Deficiency Codes</h3>
        <ResponsiveContainer width="100%" height={Math.max(250, chartData.length * 35)}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis
              type="number"
              allowDecimals={false}
              tick={{ fontSize: 11 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              type="category"
              dataKey="code"
              tick={{ fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              width={50}
            />
            <Tooltip
              formatter={(value, _name, item) => [
                value ?? 0,
                (item?.payload as { description?: string } | undefined)?.description || 'Count',
              ]}
            />
            <Bar
              dataKey="count"
              fill="#2563eb"
              radius={[0, 4, 4, 0]}
              maxBarSize={24}
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
