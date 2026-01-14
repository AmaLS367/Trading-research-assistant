import { useEffect, useState, useRef } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

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
  const [isOpen, setIsOpen] = useState(false);
  const [items, setItems] = useState<TOCItem[]>([]);
  const [activeId, setActiveId] = useState<string>('');
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
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

    function generateId(text: string): string {
      return text
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .trim();
    }

    const timeoutId = setTimeout(() => {
      const tocItems = collectHeadings();
      setItems(tocItems);

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
    }, 100);

    return () => {
      clearTimeout(timeoutId);
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, []);

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
      <div className="border-l border-border pl-4">
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
