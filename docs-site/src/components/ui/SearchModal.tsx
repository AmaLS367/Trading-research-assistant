import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Search as SearchIcon, X, FileText } from 'lucide-react';
import { useDocs } from '@/lib/docs-context';
import { createSearchIndex, search, SearchResult, SearchIndex } from '@/lib/search';
import { fetchMarkdown, extractTitle } from '@/lib/docs-manifest';
import { cn, debounce } from '@/lib/utils';

export default function SearchModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searchIndex, setSearchIndex] = useState<SearchIndex | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { lang } = useParams();
  const { manifest, languages } = useDocs();
  const navigate = useNavigate();
  
  const currentLang = lang && languages.includes(lang) ? lang : languages[0] || 'en';

  useEffect(() => {
    async function buildIndex() {
      if (!manifest || !currentLang) return;

      setIsLoading(true);
      const files = manifest.filesByLanguage[currentLang] || [];
      const pages: Array<{ title: string; slug: string; content: string }> = [];

      for (const file of files) {
        if (file.startsWith('_')) continue;

        const content = await fetchMarkdown(file);
        if (content) {
          const relativePath = file.replace(`${currentLang}/`, '');
          const title = extractTitle(content) || relativePath.replace('.md', '');
          const slug = relativePath.replace('.md', '').replace(/\/index$/, '');
          pages.push({ title, slug, content });
        }
      }

      setSearchIndex(createSearchIndex(pages));
      setIsLoading(false);
    }

    buildIndex();
  }, [manifest, currentLang]);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const performSearch = useCallback(
    debounce((q: string) => {
      if (!searchIndex || !q.trim()) {
        setResults([]);
        return;
      }
      setResults(search(searchIndex, q));
    }, 150),
    [searchIndex]
  );

  useEffect(() => {
    performSearch(query);
  }, [query, performSearch]);

  function handleSelect(slug: string) {
    navigate(`/${currentLang}/${slug}`);
    setIsOpen(false);
    setQuery('');
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          'flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm',
          'text-muted-foreground hover:bg-accent hover:text-foreground transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
        )}
      >
        <SearchIcon className="h-4 w-4" />
        <span className="hidden sm:inline">Search docs...</span>
        <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded border border-border bg-muted px-1.5 font-mono text-xs text-muted-foreground">
          ⌘K
        </kbd>
      </button>
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
      onClick={() => setIsOpen(false)}
    >
      <div
        className="fixed left-1/2 top-[20%] w-full max-w-xl -translate-x-1/2 p-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="overflow-hidden rounded-lg border border-border bg-popover shadow-2xl animate-fade-in">
          <div className="flex items-center border-b border-border px-4">
            <SearchIcon className="h-5 w-5 text-muted-foreground" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search documentation..."
              className="flex-1 bg-transparent px-4 py-4 text-base outline-none placeholder:text-muted-foreground"
            />
            <button
              onClick={() => setIsOpen(false)}
              className="rounded p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="max-h-96 overflow-y-auto p-2">
            {isLoading ? (
              <div className="p-8 text-center text-muted-foreground">
                Building search index...
              </div>
            ) : results.length > 0 ? (
              <ul>
                {results.map((result) => (
                  <li key={result.slug}>
                    <button
                      onClick={() => handleSelect(result.slug)}
                      className={cn(
                        'flex w-full items-start gap-3 rounded-md p-3 text-left',
                        'hover:bg-accent transition-colors'
                      )}
                    >
                      <FileText className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-foreground">
                          {result.title}
                        </p>
                        <p className="mt-1 truncate text-sm text-muted-foreground">
                          {result.excerpt}
                        </p>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            ) : query.trim() ? (
              <div className="p-8 text-center text-muted-foreground">
                No results found for "{query}"
              </div>
            ) : (
              <div className="p-8 text-center text-muted-foreground">
                Type to search documentation
              </div>
            )}
          </div>

          <div className="border-t border-border px-4 py-2 text-xs text-muted-foreground">
            <span className="mr-4">↑↓ Navigate</span>
            <span className="mr-4">↵ Select</span>
            <span>Esc Close</span>
          </div>
        </div>
      </div>
    </div>
  );
}
