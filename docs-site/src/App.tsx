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

  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/:lang" element={<LanguageRedirect />} />
      <Route path="/:lang/*" element={<DocsPage />} />
      <Route path="*" element={<Navigate to={`/${defaultLanguage}`} replace />} />
    </Routes>
  );
}

function LanguageRedirect() {
  const { lang } = useParams();
  const { languages, getMainDocumentSlug } = useDocs();
  const [targetSlug, setTargetSlug] = useState<string | null>(null);

  useEffect(() => {
    async function redirect() {
      if (!lang || !languages.includes(lang)) return;
      
      const mainSlug = await getMainDocumentSlug();
      setTargetSlug(mainSlug);
    }
    
    redirect();
  }, [lang, languages, getMainDocumentSlug]);

  if (targetSlug) {
    return <Navigate to={`/${lang}/${targetSlug}`} replace />;
  }

  if (lang && languages.includes(lang)) {
    return <Navigate to={`/${lang}/overview`} replace />;
  }

  return <Navigate to={`/${languages[0] || 'en'}`} replace />;
}

export default App;
