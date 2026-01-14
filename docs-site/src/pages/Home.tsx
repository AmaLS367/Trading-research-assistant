import { Link } from 'react-router-dom';
import { ArrowRight, BookOpen, Github } from 'lucide-react';
import { useDocs } from '@/lib/docs-context';
import Navbar from '@/components/layout/Navbar';
import Button from '@/components/ui/Button';

export default function Home() {
  const { navigation, currentLang } = useDocs();
  const firstPage = navigation[0]?.items[0]?.slug || 'overview';

  return (
    <div className="min-h-screen bg-background relative">
      <Navbar />
      <main className="mx-auto max-w-4xl px-4 py-24 text-center relative z-10">
        <div className="animate-fade-in">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-muted px-4 py-1.5 text-sm text-muted-foreground">
            <BookOpen className="h-4 w-4" />
            Documentation
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl md:text-6xl">
            Trading Research<br />Assistant
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
            LLM-powered trading research assistant with advanced market analysis capabilities.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link to={`/${currentLang}/${firstPage}`}>
              <Button className="gap-2">Get Started <ArrowRight className="h-4 w-4" /></Button>
            </Link>
            <a href="https://github.com" target="_blank" rel="noopener noreferrer">
              <Button variant="outline" className="gap-2"><Github className="h-4 w-4" /> GitHub</Button>
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
