import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, BookOpenCheck, RotateCcw } from 'lucide-react';
import { PageHeader } from '@/components/layout/page-header';
import { DatePicker } from '@/components/shared/date-picker';
import { EmptyState, ErrorState } from '@/components/shared';
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
} from '@/components/ui';
import { orbApi, type OrbApprovedEntry } from '@/lib/api/orb';

interface OfficeApprovedEntry extends OrbApprovedEntry {
  vessel_id: string;
  vessel_name: string;
  vessel_code: string | null;
}

interface OfficeApprovedDisplayRow {
  key: string;
  date: string;
  code: string;
  itemNo: string;
  line: string;
}

const CODE_OPTIONS = ['ALL', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'] as const;
const EN_DASH = '\u2013';
const CUBIC_METERS = `M\u00b3`;
const POSITION_REGEX = /(\d{1,3}\u00b0\d+'[NS])\s*(\d{1,3}\u00b0\d+'[EW])/;

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return 'N/A';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function getIsoDateKey(value: string | null | undefined): string {
  if (!value) {
    return '';
  }

  return String(value).slice(0, 10);
}

function sortByLatestEntry(a: OfficeApprovedEntry, b: OfficeApprovedEntry): number {
  const aTime = new Date(a.approved_at || a.date).getTime();
  const bTime = new Date(b.approved_at || b.date).getTime();
  return bTime - aTime;
}

function hasActiveFilters(fromDate: string, toDate: string, code: string): boolean {
  return Boolean(fromDate || toDate || code !== 'ALL');
}

function getItemNumber(
  entry: OfficeApprovedEntry,
  entryIndex: number,
  line: string,
  lineIndex: number
): string {
  if (lineIndex === 0) {
    return entry.item_no || '';
  }

  let itemNo = '';

  switch (entry.code) {
    case 'A':
      if (line.startsWith('TANK(S) BALLASTED')) {
        itemNo = '1';
      } else if (
        line.includes('TANK CLEANED SINCE') ||
        line.includes(`NOT CLEANED ${EN_DASH} PREVIOUS OIL`)
      ) {
        itemNo = '2';
      } else if (line.startsWith('START BALLAST')) {
        itemNo = '4.1';
      } else if (line.includes('START') && line.includes('HRS')) {
        itemNo = '3.1';
      } else if (line.startsWith('METHOD USED')) {
        itemNo = '3.2';
      } else if (line.startsWith('CLEANING WATER TO')) {
        itemNo = '3.3';
      } else if (line.includes('BALLAST QUANTITY')) {
        itemNo = '4.2';
      }
      break;

    case 'B':
      if (
        line.toUpperCase().includes('START') &&
        (line.toUpperCase().includes('POSITION') || POSITION_REGEX.test(line))
      ) {
        itemNo = '6';
      } else if (
        line.toUpperCase().includes('END') &&
        (line.toUpperCase().includes('POSITION') || POSITION_REGEX.test(line))
      ) {
        itemNo = '7';
      } else if (line.includes('KNOTS')) {
        itemNo = '8';
      } else if (line.includes('THROUGH 15 PPM EQUIPMENT')) {
        itemNo = '9.1';
      } else if (line.includes('TO RECEPTION FACILITY')) {
        itemNo = '9.2';
      } else if (line.includes(CUBIC_METERS)) {
        itemNo = '10';
      }
      break;

    case 'C':
      if (line.includes(CUBIC_METERS)) {
        itemNo = '11.2';
      }
      if (line.startsWith('RETAINED') && line.includes(CUBIC_METERS)) {
        itemNo = '11.3';
      }
      if (line.includes('COLLECTED FROM')) {
        itemNo = '11.4';
      }
      if (line.includes('RECEPTION FACILITY')) {
        itemNo = '12.1';
      } else if (line.includes('TRANSFERRED TO') && line.includes('TANK')) {
        itemNo = '12.2';
      } else if (line.includes('INCINERATED')) {
        itemNo = '12.3';
      } else if (line.includes('EVAPORATED') || line.includes('DRAINED')) {
        itemNo = '12.4';
      }
      break;

    case 'D':
      if (line.includes('START:') || line.includes('STOP:')) {
        itemNo = '14';
      } else if (line.includes('THROUGH 15 PPM EQUIPMENT')) {
        itemNo = '15.1';
      } else if (line.includes('TO PORT RECEPTION FACILITIES OF')) {
        itemNo = '15.2';
      } else if (line.includes('TRANSFERRED TO') || line.includes('RETAINED IN TANK')) {
        itemNo = '15.3';
      }
      break;

    case 'F':
      if (line.includes('FAILURE STARTED') || line.includes('FAILURE OF')) {
        itemNo = '19';
      }
      if (entryIndex === 1) {
        itemNo = '20';
      }
      if (line.trim().length > 0) {
        itemNo = '21';
      }
      break;

    case 'G':
      if (
        line.toUpperCase().includes('OCCURRENCE') ||
        line.toUpperCase().includes('TIME OF OCCURRENCE') ||
        (line.toUpperCase().includes('TIME') && (line.includes(':') || line.includes('HRS')))
      ) {
        itemNo = '22';
      } else if (
        line.toUpperCase().includes('POSITION') ||
        line.toUpperCase().includes('PLACE OR POSITION') ||
        POSITION_REGEX.test(line)
      ) {
        itemNo = '23';
      } else if (
        line.toUpperCase().includes('QUANTITY') ||
        line.toUpperCase().includes('TYPE OF OIL') ||
        line.includes(CUBIC_METERS) ||
        line.includes('MT')
      ) {
        itemNo = '24';
      } else if (line.trim().length > 0) {
        itemNo = '25';
      }
      break;

    case 'H':
      if (line.startsWith('PLACE:')) {
        itemNo = '26.1';
      } else if (
        line.startsWith('TIME:') ||
        line.includes('BUNKERING START') ||
        line.includes('BUNKERING END') ||
        line.includes('START') ||
        line.includes('END TIME')
      ) {
        itemNo = '26.2';
      } else if (line.includes('FUEL OIL BUNKERED IN TANKS')) {
        itemNo = '26.3';
      } else if (line.includes('LUBE BUNKERED IN TANKS')) {
        itemNo = '26.4';
      }
      break;

    case 'I':
      itemNo = '';
      break;

    default:
      if (line.includes(CUBIC_METERS) || line.includes('MT')) {
        itemNo = '10';
      } else if (line.startsWith('SIGNED:')) {
        itemNo = '';
      }
      break;
  }

  if (line.startsWith('SIGNED:')) {
    itemNo = '';
  }

  return itemNo;
}

function buildDisplayRows(entries: OfficeApprovedEntry[]): OfficeApprovedDisplayRow[] {
  return entries.flatMap((entry, entryIndex) => {
    const lines = (entry.record_of_operation || '')
      .split('\n')
      .filter((line) => line.trim() !== '');
    const formattedDate = formatDate(entry.date);

    return lines.map((line, lineIndex) => ({
      key: `${entry.id}-${lineIndex}`,
      date: lineIndex === 0 ? formattedDate : '',
      code: lineIndex === 0 ? entry.code : '',
      itemNo: getItemNumber(entry, entryIndex, line, lineIndex),
      line,
    }));
  });
}

export default function OfficeORBApprovedEntriesPage() {
  const [entries, setEntries] = useState<OfficeApprovedEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [partialWarning, setPartialWarning] = useState<string | null>(null);
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [selectedCode, setSelectedCode] = useState<(typeof CODE_OPTIONS)[number]>('ALL');

  const invalidDateRange = Boolean(fromDate && toDate && fromDate > toDate);

  useEffect(() => {
    let isMounted = true;

    const loadApprovedEntries = async () => {
      setIsLoading(true);
      setError(null);
      setPartialWarning(null);

      try {
        const vessels = await orbApi.fetchVessels();
        const settled = await Promise.allSettled(
          vessels.map(async (vessel) => {
            const approvedEntries = await orbApi.fetchApprovedEntries(vessel.id);
            return approvedEntries.map<OfficeApprovedEntry>((entry) => ({
              ...entry,
              vessel_id: vessel.id,
              vessel_name: vessel.vesselName || 'Unknown vessel',
              vessel_code: vessel.vesselCode,
            }));
          })
        );

        if (!isMounted) {
          return;
        }

        const successfulResults = settled
          .filter((result): result is PromiseFulfilledResult<OfficeApprovedEntry[]> => result.status === 'fulfilled')
          .flatMap((result) => result.value);
        const failedCount = settled.filter((result) => result.status === 'rejected').length;

        if (successfulResults.length === 0 && settled.length > 0) {
          throw new Error('Unable to load approved ORB entries for the office view.');
        }

        if (failedCount > 0) {
          const label = failedCount === 1 ? 'vessel' : 'vessels';
          setPartialWarning(`Unable to load approved entries for ${failedCount} ${label}. Showing partial data.`);
        }

        setEntries(successfulResults.sort(sortByLatestEntry));
      } catch (loadError) {
        if (!isMounted) {
          return;
        }

        setError(
          loadError instanceof Error
            ? loadError.message
            : 'Unable to load approved ORB entries for the office view.'
        );
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    void loadApprovedEntries();

    return () => {
      isMounted = false;
    };
  }, []);

  const filteredEntries = useMemo(() => {
    if (invalidDateRange) {
      return [];
    }

    return entries.filter((entry) => {
      const entryDate = getIsoDateKey(entry.date);

      if (fromDate && entryDate < fromDate) {
        return false;
      }

      if (toDate && entryDate > toDate) {
        return false;
      }

      if (selectedCode !== 'ALL' && entry.code !== selectedCode) {
        return false;
      }

      return true;
    });
  }, [entries, fromDate, invalidDateRange, selectedCode, toDate]);

  const displayRows = useMemo(() => buildDisplayRows(filteredEntries), [filteredEntries]);

  const clearFilters = () => {
    setFromDate('');
    setToDate('');
    setSelectedCode('ALL');
  };

  return (
    <div className="space-y-6 pb-24">
      <PageHeader
        title="e-ORB"
        subtitle="Office view of approved ORB entries across the fleet"
      />

      {partialWarning && (
        <Card className="border-warning-300 bg-warning-50">
          <CardContent className="flex items-start gap-3 p-4">
            <AlertTriangle className="mt-0.5 h-5 w-5 text-warning-700" />
            <div>
              <p className="font-medium text-warning-800">Partial results</p>
              <p className="text-sm text-warning-700">{partialWarning}</p>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Filter</CardTitle>
          <CardDescription>Filter approved entries by date range or ORB code.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="orb-office-from-date">From date</Label>
              <DatePicker
                id="orb-office-from-date"
                value={fromDate}
                onChange={setFromDate}
                maxDate={toDate || undefined}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="orb-office-to-date">To date</Label>
              <DatePicker
                id="orb-office-to-date"
                value={toDate}
                onChange={setToDate}
                minDate={fromDate || undefined}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="orb-office-code">Code</Label>
              <Select value={selectedCode} onValueChange={(value) => setSelectedCode(value as (typeof CODE_OPTIONS)[number])}>
                <SelectTrigger id="orb-office-code">
                  <SelectValue placeholder="All codes" />
                </SelectTrigger>
                <SelectContent>
                  {CODE_OPTIONS.map((code) => (
                    <SelectItem key={code} value={code}>
                      {code === 'ALL' ? 'All codes' : `Code ${code}`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {invalidDateRange && (
            <p className="text-sm text-error-600">From date cannot be later than To date.</p>
          )}

          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <p className="text-sm text-neutral-500">
              Showing {filteredEntries.length} of {entries.length} approved entries
            </p>

            <Button
              variant="outline"
              onClick={clearFilters}
              disabled={!hasActiveFilters(fromDate, toDate, selectedCode)}
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Clear filters
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Approved Entries</CardTitle>
          <CardDescription>Office users can only view approved entries. No edit or approval actions are available here.</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : error ? (
            <ErrorState
              title="Unable to load approved entries"
              message={error}
            />
          ) : displayRows.length === 0 ? (
            <EmptyState
              icon={BookOpenCheck}
              title="No approved entries found"
              description={
                invalidDateRange
                  ? 'Adjust the date range to continue.'
                  : 'No approved ORB entries match the current filters.'
              }
            />
          ) : (
            <div className="overflow-x-auto rounded-md border border-neutral-200">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-neutral-100 text-neutral-700">
                  <tr>
                    <th className="px-3 py-2">Date</th>
                    <th className="px-3 py-2">Code (Letter)</th>
                    <th className="px-3 py-2">Item (Number)</th>
                    <th className="px-3 py-2">Record of operations / signature of officer in charge</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-200 bg-white">
                  {displayRows.map((row) => (
                    <tr key={row.key} className="align-top">
                      <td className="whitespace-nowrap px-3 py-3 text-neutral-700">
                        {row.date}
                      </td>
                      <td className="px-3 py-3 text-neutral-700">{row.code}</td>
                      <td className="whitespace-nowrap px-3 py-3 text-neutral-700">
                        {row.itemNo}
                      </td>
                      <td className="whitespace-pre-line px-3 py-3 leading-6 text-neutral-700">
                        {row.line}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
