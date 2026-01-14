import { useEffect, useState, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDocs } from '@/lib/docs-context';

interface TOCItem {
  id: string;
  text: string;
  level: number;
  element: HTMLElement;
}

interface TOCProps {
  isMobile?: boolean;
}

export default function TOC({ isMobile = false }: TOCProps) {
  const location = useLocation();
  const { currentLang } = useDocs();
  const [isOpen, setIsOpen] = useState(false);
  const [items, setItems] = useState<TOCItem[]>([]);
  const [activeId, setActiveId] = useState<string>('');
  const observerRef = useRef<IntersectionObserver | null>(null);
  const retryFrameRef = useRef<number | null>(null);

  // Extract slug from location
  const pathMatch = location.pathname.match(/\/(?:en|ru|es|de|fr|ja|ko|zh)\/(.+)/);
  const slug = pathMatch ? pathMatch[1] : '';

  useEffect(() => {
    function generateId(text: string): string {
      return text
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .trim();
    }

    function collectHeadings(): TOCItem[] {
      const headings = document.querySelectorAll('article h2, article h3');
      const tocItems: TOCItem[] = [];

      headings.forEach((heading) => {
        const element = heading as HTMLElement;
        const text = element.textContent || '';
        const level = parseInt(heading.tagName.substring(1), 10);
        let id = element.id;

        if (!id) {
          id = generateId(text);
          element.id = id;
        }

        tocItems.push({ id, text, level, element });
      });

      return tocItems;
    }

    function setupObserver(tocItems: TOCItem[]) {
      if (tocItems.length === 0) return;

      if (observerRef.current) {
        observerRef.current.disconnect();
      }

      const observer = new IntersectionObserver(
        (entries) => {
          const visibleEntries = entries.filter((entry) => entry.isIntersecting);
          if (visibleEntries.length > 0) {
            const topEntry = visibleEntries.reduce((prev, current) => {
              return current.boundingClientRect.top < prev.boundingClientRect.top
                ? current
                : prev;
            });
            setActiveId(topEntry.target.id);
          }
        },
        {
          rootMargin: '-80px 0px -80% 0px',
          threshold: 0,
        }
      );

      tocItems.forEach((item) => {
        observer.observe(item.element);
      });

      observerRef.current = observer;
    }

    // Clear previous state
    setItems([]);
    setActiveId('');
    if (observerRef.current) {
      observerRef.current.disconnect();
      observerRef.current = null;
    }
    if (retryFrameRef.current !== null) {
      cancelAnimationFrame(retryFrameRef.current);
      retryFrameRef.current = null;
    }

    let retryCount = 0;
    const maxRetries = 20;

    function attemptCollection() {
      const tocItems = collectHeadings();
      
      if (tocItems.length > 0 || retryCount >= maxRetries) {
        setItems(tocItems);
        if (tocItems.length > 0) {
          setupObserver(tocItems);
        }
        retryFrameRef.current = null;
        return;
      }

      retryCount++;
      retryFrameRef.current = requestAnimationFrame(attemptCollection);
    }

    retryFrameRef.current = requestAnimationFrame(attemptCollection);

    return () => {
      if (retryFrameRef.current !== null) {
        cancelAnimationFrame(retryFrameRef.current);
        retryFrameRef.current = null;
      }
      if (observerRef.current) {
        observerRef.current.disconnect();
        observerRef.current = null;
      }
    };
  }, [slug, currentLang, location.pathname]);

  if (items.length === 0) {
    return null;
  }

  function handleClick(id: string, e: React.MouseEvent) {
    e.preventDefault();
    const element = document.getElementById(id);
    if (element) {
      const offset = 80;
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - offset;

      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth',
      });

      window.history.replaceState(null, '', `#${id}`);
    }
  }

  if (items.length === 0) {
    return null;
  }

  if (isMobile) {
    return (
      <div className="xl:hidden mb-6 border-b border-border pb-4">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex w-full items-center justify-between text-sm font-semibold text-foreground"
        >
          <span>On this page</span>
          <ChevronDown
            className={cn(
              'h-4 w-4 transition-transform',
              isOpen && 'rotate-180'
            )}
          />
        </button>
        {isOpen && (
          <nav className="mt-3 space-y-1">
            {items.map((item) => (
              <a
                key={item.id}
                href={`#${item.id}`}
                onClick={(e) => {
                  handleClick(item.id, e);
                  setIsOpen(false);
                }}
                className={cn(
                  'block text-sm transition-colors',
                  item.level === 3 && 'pl-4',
                  activeId === item.id
                    ? 'text-foreground font-medium'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {item.text}
              </a>
            ))}
          </nav>
        )}
      </div>
    );
  }

  return (
    <div className="sticky top-20 max-h-[calc(100vh-5rem)] overflow-y-auto">
      <div className="border-l border-border pl-12">
        <h3 className="text-sm font-semibold text-foreground mb-3">On this page</h3>
        <nav className="space-y-1">
          {items.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              onClick={(e) => handleClick(item.id, e)}
              className={cn(
                'block text-sm transition-colors',
                item.level === 3 && 'pl-4',
                activeId === item.id
                  ? 'text-foreground font-medium'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {item.text}
            </a>
          ))}
        </nav>
      </div>
    </div>
  );
}
