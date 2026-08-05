import { FormEvent, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Link, useLocation } from 'react-router-dom';
import {
  ArrowRight,
  BookOpenCheck,
  Bot,
  CheckCircle2,
  ClipboardList,
  FileText,
  LifeBuoy,
  Loader2,
  Search,
  Send,
  Ship,
  Sparkles,
  UserRound,
} from 'lucide-react';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Textarea,
} from '@/components/ui';
import {
  askHelpAssistant,
  getHelpStatus,
  getHelpSuggestions,
  type HelpChatContext,
  type HelpSource,
} from '@/lib/api/help';
import { getErrorMessage } from '@/lib/api/client';
import { useAuth } from '@/hooks/use-auth';
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

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: HelpSource[];
}

const helpModules: HelpModule[] = [
  {
    title: 'Inspection',
    description:
      'Inspection planning, deficiency follow-up, CARs, reports, and notifications.',
    route: ROUTES.INSPECTIONS,
    icon: Ship,
    guides: [
      {
        title: 'Office Inspection Guide',
        audience: 'Office',
        summary:
          'Dashboard review, inspection progress, deficiency tracking, and CAR closure.',
      },
      {
        title: 'Ship Inspection Guide',
        audience: 'Ship',
        summary:
          'Create inspections, update deficiencies, work on CARs, and sync vessel data.',
      },
    ],
  },
  {
    title: 'Circular',
    description:
      'Circulars, alerts, work instructions, reading status, and acknowledgements.',
    route: ROUTES.CIRCULAR,
    icon: FileText,
    guides: [
      {
        title: 'Office Circular Guide',
        audience: 'Office',
        summary:
          'Create, review, publish, track, and search circulars and alerts.',
      },
      {
        title: 'Ship Circular Guide',
        audience: 'Ship',
        summary:
          'Read documents, open PDFs, download files, and acknowledge instructions.',
      },
    ],
  },
  {
    title: 'ORB',
    description:
      'Oil Record Book entries, review states, exports, and onboard guidance.',
    route: ROUTES.ORB,
    icon: BookOpenCheck,
    guides: [
      {
        title: 'Ship ORB Guide',
        audience: 'Ship',
        summary:
          'Enter ORB records, review workflow states, export PDFs, and use guidance files.',
      },
    ],
  },
];

const helpCapabilities = [
  'Workflows',
  'Field guidance',
  'Approvals',
  'Troubleshooting',
  'Role-specific steps',
];

const defaultSuggestions = [
  'How do I create an inspection?',
  'How do I close a CAR?',
  'How does circular acknowledgement work?',
  'What should I check before syncing vessel data?',
];

function inferHelpContext(
  pathname: string
): Pick<HelpChatContext, 'module' | 'screen'> {
  if (pathname.startsWith('/inspections')) {
    return {
      module: 'inspection',
      screen: pathname.includes('/new')
        ? 'Create Inspection'
        : 'Inspection Workflow',
    };
  }
  if (pathname.startsWith('/cars')) {
    return { module: 'car', screen: 'CAR Workflow' };
  }
  if (pathname.startsWith('/circular')) {
    return { module: 'circular', screen: 'Circular Module' };
  }
  if (pathname.startsWith('/orb')) {
    return { module: 'orb', screen: 'Oil Record Book' };
  }
  if (pathname.startsWith('/safety')) {
    return { module: 'safety', screen: 'Safety Module' };
  }
  if (pathname.startsWith('/sync')) {
    return { module: 'sync', screen: 'Sync Status' };
  }
  if (pathname.startsWith('/notifications')) {
    return { module: 'notifications', screen: 'Notifications' };
  }
  return { module: 'general', screen: 'Help Center' };
}

function formatAssistantText(value: string) {
  return value
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
}

function formatModuleName(value: string) {
  return value
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function getLibraryStatus(documentsIndexed?: number) {
  if (documentsIndexed === undefined) {
    return 'Checking help library';
  }
  if (documentsIndexed <= 0) {
    return 'Help library is updating';
  }
  return `${documentsIndexed} guides available`;
}

export default function HelpPage() {
  const location = useLocation();
  const { role, vesselId } = useAuth();
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Ask me how to use VIMS. I can help with screens, fields, approvals, errors, and step-by-step workflows.',
    },
  ]);
  const formRef = useRef<HTMLFormElement>(null);

  const context = useMemo<HelpChatContext>(() => {
    const inferred = inferHelpContext(location.pathname);
    return {
      route: location.pathname,
      module: inferred.module,
      screen: inferred.screen,
      userRole: role,
      vesselId,
    };
  }, [location.pathname, role, vesselId]);

  const statusQuery = useQuery({
    queryKey: ['help-status'],
    queryFn: getHelpStatus,
  });

  const suggestionsQuery = useQuery({
    queryKey: [
      'help-suggestions',
      context.route,
      context.module,
      context.screen,
    ],
    queryFn: () => getHelpSuggestions(context),
  });

  const chatMutation = useMutation({
    mutationFn: (input: string) => askHelpAssistant(input, context),
    onSuccess: (response) => {
      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
        },
      ]);
    },
    onError: (error) => {
      setMessages((current) => [
        ...current,
        {
          id: `assistant-error-${Date.now()}`,
          role: 'assistant',
          content: getErrorMessage(error),
        },
      ]);
    },
  });

  function submitQuestion(value: string) {
    const trimmed = value.trim();
    if (!trimmed || chatMutation.isPending) {
      return;
    }
    setMessages((current) => [
      ...current,
      { id: `user-${Date.now()}`, role: 'user', content: trimmed },
    ]);
    setQuestion('');
    chatMutation.mutate(trimmed);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    submitQuestion(question);
  }

  const suggestedQuestions =
    suggestionsQuery.data && suggestionsQuery.data.length > 0
      ? suggestionsQuery.data
      : defaultSuggestions;

  return (
    <RootLayout>
      <PageHeader
        title="Help Center"
        subtitle="Ask practical questions about VIMS workflows, screens, fields, and approvals."
      />

      <div className="space-y-6 pb-24">
        <section className="rounded-lg border border-neutral-200 bg-white shadow-sm">
          <div className="grid gap-0 lg:grid-cols-[minmax(0,1fr)_320px]">
            <div className="border-b border-neutral-200 p-5 md:p-6 lg:border-b-0 lg:border-r">
              <div className="flex max-w-4xl flex-col gap-4">
                <div className="inline-flex w-fit items-center gap-2 rounded-md border border-primary-200 bg-primary-50 px-3 py-1.5 text-xs font-semibold uppercase text-primary-700">
                  <LifeBuoy className="h-4 w-4" />
                  VIMS help
                </div>
                <div>
                  <h2 className="text-2xl font-semibold leading-8 text-neutral-900">
                    Find the right step without reading the full manual.
                  </h2>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-neutral-600">
                    Type a question in normal language. The assistant checks the
                    help guides and gives a short answer with the most relevant
                    references.
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {helpCapabilities.map((item) => (
                    <span
                      key={item}
                      className="inline-flex items-center gap-1.5 rounded-md border border-neutral-200 bg-neutral-50 px-3 py-1.5 text-xs font-medium text-neutral-700"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5 text-success-600" />
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-neutral-50 p-5 md:p-6">
              <div className="space-y-3">
                <div className="rounded-lg border border-neutral-200 bg-white p-4">
                  <p className="text-xs font-medium uppercase text-neutral-500">
                    Help library
                  </p>
                  <p className="mt-2 text-lg font-semibold text-neutral-900">
                    {getLibraryStatus(statusQuery.data?.documents_indexed)}
                  </p>
                </div>
                <div className="rounded-lg border border-neutral-200 bg-white p-4">
                  <p className="text-xs font-medium uppercase text-neutral-500">
                    Current page
                  </p>
                  <p className="mt-2 text-sm font-semibold text-neutral-900">
                    {context.screen}
                  </p>
                  <p className="mt-1 text-xs text-neutral-500">
                    {formatModuleName(context.module ?? 'general')} guidance is
                    prioritized.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
          <Card className="overflow-hidden border-neutral-200 shadow-sm">
            <CardHeader className="border-b border-neutral-200 bg-white p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <Bot className="h-5 w-5 text-primary-600" />
                    Ask VIMS Help
                  </CardTitle>
                  <CardDescription className="mt-1">
                    Answers are based on the available VIMS help guides.
                  </CardDescription>
                </div>
                <Badge variant="success" className="w-fit">
                  Ready
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="p-0">
              <div className="max-h-[620px] min-h-[440px] space-y-4 overflow-y-auto bg-neutral-50 p-4 md:p-5">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={
                      message.role === 'user'
                        ? 'ml-auto max-w-[88%] rounded-lg bg-primary-600 px-4 py-3 text-sm leading-6 text-white shadow-sm'
                        : 'max-w-[92%] rounded-lg border border-neutral-200 bg-white px-4 py-3 text-sm leading-6 text-neutral-700 shadow-sm'
                    }
                  >
                    <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase text-current opacity-80">
                      {message.role === 'user' ? (
                        <UserRound className="h-3.5 w-3.5" />
                      ) : (
                        <Bot className="h-3.5 w-3.5" />
                      )}
                      {message.role === 'user' ? 'You' : 'Help'}
                    </div>

                    <div className="space-y-2">
                      {formatAssistantText(message.content).map((paragraph) => (
                        <p key={paragraph}>{paragraph}</p>
                      ))}
                    </div>

                    {message.sources?.length ? (
                      <div className="mt-4 border-t border-neutral-200 pt-3">
                        <p className="mb-2 text-xs font-semibold uppercase text-neutral-500">
                          Related guides
                        </p>
                        <div className="grid gap-2 md:grid-cols-2">
                          {message.sources.slice(0, 4).map((source) => (
                            <div
                              key={source.id}
                              className="rounded-lg border border-neutral-200 bg-neutral-50 px-3 py-2"
                            >
                              <p className="text-xs font-semibold leading-5 text-neutral-800">
                                {source.title}
                              </p>
                              <p className="mt-1 text-xs text-neutral-500">
                                {formatModuleName(source.module)}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </div>
                ))}

                {chatMutation.isPending ? (
                  <div className="flex max-w-[92%] items-center gap-3 rounded-lg border border-neutral-200 bg-white px-4 py-3 text-sm text-neutral-500 shadow-sm">
                    <div className="rounded-md bg-primary-50 p-2 text-primary-600">
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                    <div>
                      <p className="font-medium text-neutral-800">
                        Looking through the help guides
                      </p>
                      <p className="text-xs text-neutral-500">
                        Finding the most relevant steps for your question.
                      </p>
                    </div>
                  </div>
                ) : null}
              </div>

              <div className="border-t border-neutral-200 bg-white p-4 md:p-5">
                <form
                  ref={formRef}
                  onSubmit={handleSubmit}
                  className="flex flex-col gap-3 md:flex-row"
                >
                  <Textarea
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="Ask about a VIMS workflow, field, approval, or error..."
                    className="min-h-[76px] resize-none text-sm"
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        formRef.current?.requestSubmit();
                      }
                    }}
                  />
                  <Button
                    type="submit"
                    className="md:h-[76px] md:w-28"
                    disabled={chatMutation.isPending}
                  >
                    {chatMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <Send className="mr-2 h-4 w-4" />
                        Ask
                      </>
                    )}
                  </Button>
                </form>
              </div>
            </CardContent>
          </Card>

          <aside className="space-y-4">
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Sparkles className="h-4 w-4 text-primary-600" />
                  Quick Questions
                </CardTitle>
                <CardDescription>
                  Start with a common help request.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {suggestedQuestions.slice(0, 5).map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => submitQuestion(suggestion)}
                    className="flex w-full items-start justify-between gap-3 rounded-lg border border-neutral-200 bg-white px-3 py-2.5 text-left text-sm leading-5 text-neutral-700 transition-colors hover:border-primary-300 hover:bg-primary-50"
                  >
                    <span>{suggestion}</span>
                    <ArrowRight className="mt-0.5 h-4 w-4 shrink-0 text-neutral-400" />
                  </button>
                ))}
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <ClipboardList className="h-4 w-4 text-primary-600" />
                  Module Guides
                </CardTitle>
                <CardDescription>
                  Open a module and continue from there.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {helpModules.map((module) => {
                  const Icon = module.icon;
                  return (
                    <div
                      key={module.title}
                      className="rounded-lg border border-neutral-200 bg-white p-3 transition-colors hover:border-primary-200 hover:bg-primary-50"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex min-w-0 items-start gap-3">
                          <div className="rounded-md bg-neutral-100 p-2 text-neutral-700">
                            <Icon className="h-4 w-4" />
                          </div>
                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-neutral-900">
                              {module.title}
                            </p>
                            <p className="mt-1 text-xs leading-5 text-neutral-500">
                              {module.description}
                            </p>
                          </div>
                        </div>
                        <Button
                          asChild
                          variant="ghost"
                          size="icon"
                          className="shrink-0"
                        >
                          <Link
                            to={module.route}
                            aria-label={`Open ${module.title}`}
                          >
                            <ArrowRight className="h-4 w-4" />
                          </Link>
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </aside>

          <section className="xl:col-span-2">
            <div className="mb-3 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
              <div>
                <div className="flex items-center gap-2 text-sm font-semibold text-neutral-800">
                  <Search className="h-4 w-4" />
                  Browse Help Guides
                </div>
                <p className="mt-1 text-sm text-neutral-500">
                  Use these shortcuts when you want to open the module directly.
                </p>
              </div>
            </div>
            <div className="grid gap-4 xl:grid-cols-3">
              {helpModules.map((module) => {
                const Icon = module.icon;

                return (
                  <Card
                    key={module.title}
                    className="border-neutral-200 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
                  >
                    <CardHeader className="space-y-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <div className="rounded-lg bg-primary-50 p-3 text-primary-700">
                            <Icon className="h-5 w-5" />
                          </div>
                          <div>
                            <CardTitle>{module.title}</CardTitle>
                            <CardDescription className="mt-1">
                              {module.description}
                            </CardDescription>
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
                        <div
                          key={guide.title}
                          className="rounded-lg border border-neutral-200 bg-neutral-50 p-4"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <h3 className="text-sm font-semibold text-neutral-900">
                              {guide.title}
                            </h3>
                            <Badge variant="outline">{guide.audience}</Badge>
                          </div>
                          <p className="mt-2 text-sm leading-6 text-neutral-600">
                            {guide.summary}
                          </p>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </section>
        </div>
      </div>
    </RootLayout>
  );
}
