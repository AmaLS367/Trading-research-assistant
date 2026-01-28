import { Link, useParams } from 'react-router-dom';
import {
  ArrowRight,
  BookOpen,
  Github,
  FileText,
  Code,
  LineChart,
  Plug,
  Layers,
  ShieldCheck,
  Terminal,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useDocs } from '@/lib/docs-context';
import Navbar from '@/components/layout/Navbar';
import Button from '@/components/ui/Button';
import { cn } from '@/lib/utils';

const content = {
  en: {
    hero: {
      badge: '📚 Documentation',
      subtitle: 'LLM-powered market research assistant with clean architecture and extensible providers.',
      getStarted: 'Get Started',
      github: 'GitHub',
      terminal: {
        prompt: '$',
        commands: [
          { text: 'python -m src.app.main --help', type: 'command' },
          { text: 'Usage: main.py [OPTIONS]', type: 'output' },
          { text: 'Options:', type: 'output' },
          { text: '  --help  Show this message and exit.', type: 'output' },
        ],
      },
    },
    startHere: {
      title: '🚀 Start here',
      cards: [
        {
          slug: 'overview',
          title: 'Overview',
          description: 'What it is and what it can do.',
          icon: BookOpen,
        },
        {
          slug: 'usage_guide',
          title: 'Usage Guide',
          description: 'Install, configure, run.',
          icon: FileText,
        },
        {
          slug: 'architecture',
          title: 'Architecture',
          description: 'Modules, layers, rules.',
          icon: Code,
        },
      ],
    },
    highlights: {
      title: '✨ Highlights',
      items: [
        {
          text: 'Technical analysis + news synthesis',
          icon: LineChart,
        },
        {
          text: 'Pluggable data and news providers',
          icon: Plug,
        },
        {
          text: 'Clean Architecture module boundaries',
          icon: Layers,
        },
        {
          text: 'Safety policy and validation constraints',
          icon: ShieldCheck,
        },
        {
          text: 'CLI-first workflow for automation',
          icon: Terminal,
        },
      ],
    },
  },
  ru: {
    hero: {
      badge: '📚 Документация',
      subtitle: 'LLM ассистент для ресерча рынка с чистой архитектурой и расширяемыми провайдерами.',
      getStarted: 'Начать',
      github: 'GitHub',
      terminal: {
        prompt: '$',
        commands: [
          { text: 'python -m src.app.main --help', type: 'command' },
          { text: 'Usage: main.py [OPTIONS]', type: 'output' },
          { text: 'Options:', type: 'output' },
          { text: '  --help  Show this message and exit.', type: 'output' },
        ],
      },
    },
    startHere: {
      title: '🚀 Начните здесь',
      cards: [
        {
          slug: 'overview',
          title: 'Обзор',
          description: 'Что это и что умеет.',
          icon: BookOpen,
        },
        {
          slug: 'usage_guide',
          title: 'Гайд',
          description: 'Установка, настройка, запуск.',
          icon: FileText,
        },
        {
          slug: 'architecture',
          title: 'Архитектура',
          description: 'Модули, слои, правила.',
          icon: Code,
        },
      ],
    },
    highlights: {
      title: '✨ Highlights',
      items: [
        {
          text: 'Теханализ + новости в одном пайплайне',
          icon: LineChart,
        },
        {
          text: 'Подключаемые провайдеры данных и новостей',
          icon: Plug,
        },
        {
          text: 'Четкие границы модулей Clean Architecture',
          icon: Layers,
        },
        {
          text: 'Safety политика и ограничения валидации',
          icon: ShieldCheck,
        },
        {
          text: 'CLI-first для автоматизации',
          icon: Terminal,
        },
      ],
    },
  },
};

export default function Home() {
  const { lang } = useParams();
  const { navigation, languages } = useDocs();
  const [, forceUpdate] = useState(0);

  const storedLang = typeof window !== 'undefined' ? localStorage.getItem('docs_site_lang') : null;
  const currentLang = lang && languages.includes(lang)
    ? lang
    : storedLang && languages.includes(storedLang)
      ? storedLang
      : languages[0] || 'en';

  // Listen for language changes
  useEffect(() => {
    function handleLanguageChange() {
      forceUpdate((prev) => prev + 1);
    }

    window.addEventListener('languageChanged', handleLanguageChange);

    return () => {
      window.removeEventListener('languageChanged', handleLanguageChange);
    };
  }, []);

  const langContent = content[currentLang as keyof typeof content] || content.en;
  const firstPage = navigation[0]?.items[0]?.slug || 'overview';

  // Find actual navigation items for start here cards
  const allNavItems = navigation.flatMap((group) => group.items);
  const startHereCards = langContent.startHere.cards
    .map((card) => {
      const navItem = allNavItems.find((item) => item.slug === card.slug);
      if (!navItem) return null;
      return {
        ...card,
        title: navItem.title,
        slug: navItem.slug,
      };
    })
    .filter((card): card is NonNullable<typeof card> => card !== null);

  // Disable body scroll and enable internal scroll on HomePage
  useEffect(() => {
    document.documentElement.classList.add('overflow-hidden');
    document.body.classList.add('overflow-hidden');

    return () => {
      document.documentElement.classList.remove('overflow-hidden');
      document.body.classList.remove('overflow-hidden');
    };
  }, []);

  return (
    <div className="bg-background relative overflow-hidden">
      {/* Background overlay with gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-muted/5 pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,hsl(var(--muted)/0.08)_0%,transparent_50%)] pointer-events-none" />

      <Navbar />
      <main
        className="w-full px-4 md:px-8 lg:px-12 py-6 md:py-8 relative z-10 overflow-y-auto overflow-x-hidden scrollbar-hidden"
        style={{ height: 'calc(100vh - 64px)' }}
      >
        <div className="max-w-7xl mx-auto">
          {/* Hero Section - 2 columns */}
          <section className="mb-6 md:mb-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center">
              {/* Left: Text content */}
              <div className="animate-fade-in">
                <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-muted px-4 py-1.5 text-sm text-muted-foreground">
                  <BookOpen className="h-4 w-4" />
                  {langContent.hero.badge}
                </div>
                <h1 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl mb-4 text-foreground">
                  Trading Research Assistant
                </h1>
                <p className="text-base md:text-lg text-muted-foreground mb-6 max-w-xl leading-relaxed">
                  {langContent.hero.subtitle}
                </p>
                <div className="flex flex-col sm:flex-row items-start gap-3">
                  <Link to={`/${currentLang}/${firstPage}`}>
                    <Button
                      className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90"
                    >
                      {langContent.hero.getStarted} <ArrowRight className="h-4 w-4" />
                    </Button>
                  </Link>
                  <a
                    href="https://github.com/AmaLS367/Trading-research-assistant"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Button variant="outline" className="gap-2">
                      <Github className="h-4 w-4" /> {langContent.hero.github}
                      <span className="ml-1 text-xs text-muted-foreground">★ Stars</span>
                    </Button>
                  </a>
                </div>
              </div>

              {/* Right: Terminal preview */}
              <div className="animate-fade-in">
                <div className="bg-surface-elevated/80 backdrop-blur-sm border border-border/50 rounded-lg p-4 shadow-lg">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="flex gap-1.5">
                      <div className="w-3 h-3 rounded-full bg-destructive/60" />
                      <div className="w-3 h-3 rounded-full bg-warning/60" />
                      <div className="w-3 h-3 rounded-full bg-success/60" />
                    </div>
                    <span className="text-xs text-muted-foreground ml-2 font-mono">
                      terminal
                    </span>
                  </div>
                  <div className="space-y-1 font-mono text-sm">
                    {langContent.hero.terminal.commands.map((cmd, idx) => (
                      <div
                        key={idx}
                        className={cn(
                          cmd.type === 'command' ? 'text-foreground' : 'text-muted-foreground'
                        )}
                      >
                        {cmd.type === 'command' && (
                          <span className="text-muted-foreground">
                            {langContent.hero.terminal.prompt}{' '}
                          </span>
                        )}
                        {cmd.text}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Main Content Grid: Start here + Highlights */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
            {/* Start here Section */}
            {startHereCards.length > 0 && (
              <section>
                <h2 className="text-lg font-semibold text-muted-foreground mb-6">
                  {langContent.startHere.title}
                </h2>
                <div className="grid grid-cols-1 gap-4">
                  {startHereCards.map((card) => {
                    const Icon = card.icon;
                    return (
                      <Link
                        key={card.slug}
                        to={`/${currentLang}/${card.slug}`}
                        className={cn(
                          'group block bg-surface/60 backdrop-blur-sm border border-border/50 rounded-lg p-5',
                          'transition-all cursor-pointer',
                          'hover:border-primary/30 hover:shadow-md hover:-translate-y-0.5'
                        )}
                      >
                        <div className="flex items-start gap-4">
                          <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-muted/50 flex items-center justify-center text-foreground group-hover:bg-primary/10 transition-colors">
                            <Icon className="h-5 w-5 stroke-[1.5]" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-semibold text-foreground mb-1.5 group-hover:text-primary transition-colors">
                              {card.title}
                            </h3>
                            <p className="text-sm text-muted-foreground">{card.description}</p>
                          </div>
                        </div>
                      </Link>
                    );
                  })}
                </div>
              </section>
            )}

            {/* Highlights Section */}
            <section>
              <h2 className="text-lg font-semibold text-muted-foreground mb-6">
                {langContent.highlights.title}
              </h2>
              <div className="grid grid-cols-1 gap-3">
                {langContent.highlights.items.map((item, index) => {
                  const Icon = item.icon;
                  return (
                    <div
                      key={index}
                      className="flex items-start gap-3 bg-surface/40 backdrop-blur-sm border border-border/30 rounded-lg p-3"
                    >
                      <div className="flex-shrink-0 w-8 h-8 rounded-md bg-muted/50 flex items-center justify-center text-primary mt-0.5">
                        <Icon className="h-4 w-4 stroke-[1.5]" />
                      </div>
                      <p className="text-sm text-muted-foreground pt-1">{item.text}</p>
                    </div>
                  );
                })}
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
