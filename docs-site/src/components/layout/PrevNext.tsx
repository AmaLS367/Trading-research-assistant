import { Link, useParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useDocs } from '@/lib/docs-context';
import { cn } from '@/lib/utils';

interface PrevNextProps {
  currentSlug: string;
}

export default function PrevNext({ currentSlug }: PrevNextProps) {
  const { lang } = useParams();
  const { navigation, languages } = useDocs();
  
  const currentLang = lang && languages.includes(lang) ? lang : languages[0] || 'en';

  const allItems = navigation.flatMap((group) => group.items);
  const currentIndex = allItems.findIndex((item) => item.slug === currentSlug);

  const prev = currentIndex > 0 ? allItems[currentIndex - 1] : null;
  const next = currentIndex < allItems.length - 1 ? allItems[currentIndex + 1] : null;

  if (!prev && !next) return null;

  return (
    <nav className="mt-12 flex items-stretch gap-4 border-t border-border pt-8">
      {prev ? (
        <Link
          to={`/${currentLang}/${prev.slug}`}
          className={cn(
            'group flex flex-1 flex-col items-start rounded-lg border border-border p-4',
            'hover:border-foreground/20 hover:bg-accent transition-colors'
          )}
        >
          <span className="flex items-center gap-1 text-sm text-muted-foreground">
            <ChevronLeft className="h-4 w-4" />
            Previous
          </span>
          <span className="mt-1 font-medium text-foreground group-hover:text-foreground">
            {prev.title}
          </span>
        </Link>
      ) : (
        <div className="flex-1" />
      )}

      {next ? (
        <Link
          to={`/${currentLang}/${next.slug}`}
          className={cn(
            'group flex flex-1 flex-col items-end rounded-lg border border-border p-4',
            'hover:border-foreground/20 hover:bg-accent transition-colors'
          )}
        >
          <span className="flex items-center gap-1 text-sm text-muted-foreground">
            Next
            <ChevronRight className="h-4 w-4" />
          </span>
          <span className="mt-1 font-medium text-foreground group-hover:text-foreground">
            {next.title}
          </span>
        </Link>
      ) : (
        <div className="flex-1" />
      )}
    </nav>
  );
}
