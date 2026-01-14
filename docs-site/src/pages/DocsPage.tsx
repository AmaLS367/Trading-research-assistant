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
  const { languages, getPageContent, getMainDocumentSlug, navigation } = useDocs();
  const [content, setContent] = useState<{ markdown: string; title: string } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  // Language always comes from URL
  const currentLang = lang && languages.includes(lang) ? lang : languages[0] || 'en';

  const pathSlug = location.pathname.replace(`/${lang}/`, '').replace(/^\//, '');
  const slug = pathSlug || navigation[0]?.items[0]?.slug || 'overview';

  useEffect(() => {
    async function loadContent() {
      if (!slug || !currentLang) return;
      setIsLoading(true);
      setNotFound(false);
      
      // Pass currentLang from URL explicitly to getPageContent
      const page = await getPageContent(slug, currentLang);
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

  useEffect(() => {
    async function handleLanguageRedirect() {
      if (lang && !languages.includes(lang)) {
        return;
      }
      
      if (!pathSlug && lang && languages.includes(lang)) {
        const mainSlug = await getMainDocumentSlug(lang);
        if (mainSlug) {
          window.location.hash = `#/${lang}/${mainSlug}`;
        }
      }
    }
    
    handleLanguageRedirect();
  }, [lang, languages, pathSlug, getMainDocumentSlug]);

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
        <article className="animate-fade-in p-6 md:p-8 lg:p-10">
          <Breadcrumbs />
          <MarkdownRenderer
            key={`${currentLang}:${slug}`}
            content={content.markdown}
            currentLang={currentLang}
            currentSlug={slug}
          />
          <PrevNext currentSlug={slug} />
        </article>
      ) : null}
    </DocsLayout>
  );
}
