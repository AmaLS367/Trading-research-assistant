import { Routes, Route, Navigate, useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useDocs } from './lib/docs-context';
import Home from './pages/Home';
import DocsPage from './pages/DocsPage';
import NotFound from './pages/NotFound';
import LoadingScreen from './components/ui/LoadingScreen';

function App() {
  const { isLoading, languages, defaultLanguage } = useDocs();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (languages.length === 0) {
    return <NotFound message="No documentation found. Please add markdown files to the docs/ directory." />;
  }

  const getDefaultRoute = () => {
    const storedLang = typeof window !== 'undefined' ? localStorage.getItem('docs_site_lang') : null;
    const effectiveLang = storedLang && languages.includes(storedLang) ? storedLang : defaultLanguage;
    return `/${effectiveLang}`;
  };

  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/:lang" element={<LanguageRedirect />} />
      <Route path="/:lang/*" element={<DocsPage />} />
      <Route path="*" element={<Navigate to={getDefaultRoute()} replace />} />
    </Routes>
  );
}

function LanguageRedirect() {
  const { lang } = useParams();
  const { languages, getMainDocumentSlug } = useDocs();
  const [targetSlug, setTargetSlug] = useState<string | null>(null);

  useEffect(() => {
    async function redirect() {
      let effectiveLang = lang;
      
      // If lang is missing or invalid, check localStorage
      if (!effectiveLang || !languages.includes(effectiveLang)) {
        const storedLang = typeof window !== 'undefined' ? localStorage.getItem('docs_site_lang') : null;
        if (storedLang && languages.includes(storedLang)) {
          effectiveLang = storedLang;
        } else {
          effectiveLang = languages[0] || 'en';
        }
      }
      
      if (!effectiveLang || !languages.includes(effectiveLang)) return;
      
      const mainSlug = await getMainDocumentSlug(effectiveLang);
      setTargetSlug(mainSlug);
    }
    
    redirect();
  }, [lang, languages, getMainDocumentSlug]);

  if (targetSlug) {
    const effectiveLang = lang && languages.includes(lang) 
      ? lang 
      : (typeof window !== 'undefined' && localStorage.getItem('docs_site_lang') && languages.includes(localStorage.getItem('docs_site_lang')!)
          ? localStorage.getItem('docs_site_lang')!
          : languages[0] || 'en');
    return <Navigate to={`/${effectiveLang}/${targetSlug}`} replace />;
  }

  const effectiveLang = lang && languages.includes(lang) 
    ? lang 
    : (typeof window !== 'undefined' && localStorage.getItem('docs_site_lang') && languages.includes(localStorage.getItem('docs_site_lang')!)
        ? localStorage.getItem('docs_site_lang')!
        : languages[0] || 'en');

  if (effectiveLang && languages.includes(effectiveLang)) {
    return <Navigate to={`/${effectiveLang}/overview`} replace />;
  }

  return <Navigate to={`/${languages[0] || 'en'}`} replace />;
}

export default App;
