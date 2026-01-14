import { useEffect, useState } from 'react';
import { useParams, useLocation, Navigate } from 'react-router-dom';
import { useDocs } from '@/lib/docs-context';
import DocsLayout from '@/components/layout/DocsLayout';
import Breadcrumbs from '@/components/layout/Breadcrumbs';
import PrevNext from '@/components/layout/PrevNext';
import MarkdownRenderer from '@/features/docs/MarkdownRenderer';
import { Loader2 } from 'lucide-react';

export default function DocsPage() {
  const { lang } = useParams();
  const location = useLocation();
  const { languages, currentLang, setCurrentLang, getPageContent, navigation } = useDocs();
  const [content, setContent] = useState<{ markdown: string; title: string } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const slug = location.pathname.replace(`/${lang}/`, '').replace(/^\//, '') || navigation[0]?.items[0]?.slug || 'overview';

  useEffect(() => {
    if (lang && languages.includes(lang) && lang !== currentLang) {
      setCurrentLang(lang);
    }
  }, [lang, languages, currentLang, setCurrentLang]);

  useEffect(() => {
    async function loadContent() {
      if (!slug) return;
      setIsLoading(true);
      setNotFound(false);
      const page = await getPageContent(slug);
      if (page) {
        setContent(page);
        document.title = `${page.title} - Trading Research Assistant`;
      } else {
        setNotFound(true);
      }
      setIsLoading(false);
    }
    loadContent();
  }, [slug, getPageContent, currentLang]);

  if (lang && !languages.includes(lang)) {
    return <Navigate to={`/${languages[0] || 'en'}`} replace />;
  }

  return (
    <DocsLayout>
      {isLoading ? (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : notFound ? (
        <div className="py-24 text-center">
          <h1 className="text-2xl font-bold text-foreground">Page not found</h1>
          <p className="mt-2 text-muted-foreground">The requested documentation page could not be found.</p>
        </div>
      ) : content ? (
        <article className="animate-fade-in">
          <Breadcrumbs />
          <MarkdownRenderer content={content.markdown} />
          <PrevNext currentSlug={slug} />
        </article>
      ) : null}
    </DocsLayout>
  );
}
