import { Routes, Route, Navigate } from 'react-router-dom';
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
      <Route path="/:lang/*" element={<DocsPage />} />
      <Route path="*" element={<Navigate to={`/${defaultLanguage}`} replace />} />
    </Routes>
  );
}

export default App;
