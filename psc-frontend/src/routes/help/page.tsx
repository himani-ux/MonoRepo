import { Link } from 'react-router-dom';
import { ArrowRight, BookOpenCheck, Building2, FileText, LifeBuoy, Ship } from 'lucide-react';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import { Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui';
import { ROUTES } from '@/lib/utils/constants';

interface HelpGuide {
  title: string;
  audience: 'Office' | 'Ship';
  summary: string;
}

interface HelpModule {
  title: string;
  description: string;
  route: string;
  icon: typeof Ship;
  guides: HelpGuide[];
}

const helpModules: HelpModule[] = [
  {
    title: 'Inspection',
    description: 'Inspection, deficiency, CAR, report, notification, and settings guidance.',
    route: ROUTES.INSPECTIONS,
    icon: Ship,
    guides: [
      {
        title: 'Office Inspection User Guide',
        audience: 'Office',
        summary: 'Dashboard, inspections, deficiencies, CARs, reports, notifications, and settings.',
      },
      {
        title: 'Ship Inspection User Guide',
        audience: 'Ship',
        summary: 'Create inspections, manage deficiencies, work on CARs, and sync vessel data.',
      },
    ],
  },
  {
    title: 'Circular',
    description: 'Circular, alert, and work-instruction guidance for office and vessel users.',
    route: ROUTES.CIRCULAR,
    icon: FileText,
    guides: [
      {
        title: 'Office Circular User Guide',
        audience: 'Office',
        summary: 'Create, review, publish, track, and search circulars, alerts, and work instructions.',
      },
      {
        title: 'Ship Circular User Guide',
        audience: 'Ship',
        summary: 'Read documents, open PDFs, download files, and acknowledge circulars on board.',
      },
    ],
  },
  {
    title: 'ORB',
    description: 'Oil Record Book help for ship-side workflows and guidance documents.',
    route: ROUTES.ORB,
    icon: BookOpenCheck,
    guides: [
      {
        title: 'Ship ORB User Guide',
        audience: 'Ship',
        summary: 'Enter ORB records, review workflow states, export PDFs, and use guideline documents.',
      },
    ],
  },
];

const supportNotes = [
  'This Help area is now arranged module-wise so the full guides can be slotted in gradually.',
  'Role-based visibility still applies. Some actions mentioned in a guide will only show for allowed logins.',
  'Guide rendering and document embedding can be added next once you decide the final module grouping.',
];

export default function HelpPage() {
  return (
    <RootLayout>
      <PageHeader
        title="Help Center"
        subtitle="A single place for module-wise user guides and workflow references."
      />

      <div className="space-y-6 pb-24">
        <Card className="border-primary-100 bg-gradient-to-r from-white to-primary-50/70">
          <CardContent className="flex flex-col gap-4 p-6 md:flex-row md:items-start md:justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-primary-700">
                <LifeBuoy className="h-5 w-5" />
                <span className="text-sm font-medium">Help section scaffolded</span>
              </div>
              <h2 className="text-lg font-semibold text-neutral-900">
                Guides are grouped by module and ready for structured content.
              </h2>
              <p className="max-w-3xl text-sm leading-6 text-neutral-600">
                For now this screen gives users a clean entry point to the available guide sets.
                As you finalize each module, the detailed steps, screenshots, and files can be
                placed under the matching card below.
              </p>
            </div>

            <div className="rounded-xl border border-primary-100 bg-white/90 p-4 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-primary-50 p-2 text-primary-600">
                  <Building2 className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-neutral-400">Current layout</p>
                  <p className="text-sm font-semibold text-neutral-800">Module-wise help hub</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <section className="grid gap-4 xl:grid-cols-3">
          {helpModules.map((module) => {
            const Icon = module.icon;

            return (
              <Card key={module.title} className="border-neutral-200">
                <CardHeader className="space-y-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="rounded-xl bg-neutral-100 p-3 text-neutral-700">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <CardTitle>{module.title}</CardTitle>
                        <CardDescription className="mt-1">{module.description}</CardDescription>
                      </div>
                    </div>
                    <Button asChild variant="outline" size="sm">
                      <Link to={module.route}>
                        Open
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </Link>
                    </Button>
                  </div>
                </CardHeader>

                <CardContent className="space-y-3">
                  {module.guides.map((guide) => (
                    <div key={guide.title} className="rounded-xl border border-neutral-200 bg-neutral-50 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <h3 className="text-sm font-semibold text-neutral-900">{guide.title}</h3>
                        <Badge variant="outline">{guide.audience}</Badge>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-neutral-600">{guide.summary}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            );
          })}
        </section>

        <Card>
          <CardHeader>
            <CardTitle>Notes For Guide Arrangement</CardTitle>
            <CardDescription>
              This section explains how the help hub is prepared for your next content pass.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {supportNotes.map((note) => (
              <div key={note} className="rounded-lg border border-neutral-200 bg-white p-4 text-sm text-neutral-600">
                {note}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </RootLayout>
  );
}
