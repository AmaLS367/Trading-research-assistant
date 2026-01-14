import { Link, useParams, useNavigate, useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { Github, Menu, X } from 'lucide-react';
import { useDocs } from '@/lib/docs-context';
import { getLanguageDisplayName } from '@/lib/utils';
import ThemeToggle from '../ui/ThemeToggle';
import Dropdown from '../ui/Dropdown';
import SearchModal from '../ui/SearchModal';
import Button from '../ui/Button';

interface NavbarProps {
  showSidebar?: boolean;
  onMenuClick?: () => void;
  isMobileMenuOpen?: boolean;
}

export default function Navbar({
  showSidebar = false,
  onMenuClick,
  isMobileMenuOpen,
}: NavbarProps) {
  const { lang } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { languages, getMainDocumentSlug } = useDocs();
  
  // Check if we're on HomePage
  const hashMatch = location.hash.match(/^#\/(?:en|ru|es|de|fr|ja|ko|zh)\/(.+)/);
  const pathMatch = location.pathname.match(/\/(?:en|ru|es|de|fr|ja|ko|zh)\/(.+)/);
  const isHomePage = !hashMatch && !pathMatch && (location.pathname === '/' || location.hash === '' || location.hash === '#/');
  
  // Get current language: from URL on DocsPage, from localStorage on HomePage
  let currentLangFromUrl = lang && languages.includes(lang) ? lang : null;
  if (!currentLangFromUrl && isHomePage) {
    // On HomePage, use language from localStorage
    const storedLang = typeof window !== 'undefined' ? localStorage.getItem('docs_site_lang') : null;
    currentLangFromUrl = storedLang && languages.includes(storedLang) ? storedLang : languages[0] || 'en';
  } else if (!currentLangFromUrl) {
    // On DocsPage without lang in URL, fallback to default
    currentLangFromUrl = languages[0] || 'en';
  }

  const languageOptions = languages.map((lang) => ({
    value: lang,
    label: getLanguageDisplayName(lang),
  }));

  // Force re-render when language changes on HomePage
  const [updateKey, setUpdateKey] = useState(0);
  useEffect(() => {
    function handleLanguageChange() {
      setUpdateKey((prev) => prev + 1);
    }

    window.addEventListener('languageChanged', handleLanguageChange);

    return () => {
      window.removeEventListener('languageChanged', handleLanguageChange);
    };
  }, []);

  // Recalculate currentLangFromUrl on every render, especially after language change
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const effectiveCurrentLang = (() => {
    let lang = currentLangFromUrl;
    if (isHomePage && updateKey >= 0) {
      // On HomePage, always read fresh from localStorage
      const storedLang = typeof window !== 'undefined' ? localStorage.getItem('docs_site_lang') : null;
      lang = storedLang && languages.includes(storedLang) ? storedLang : languages[0] || 'en';
    }
    return lang;
  })();

  async function handleLanguageChange(newLang: string) {
    if (newLang === effectiveCurrentLang) return;

    // Save to localStorage
    localStorage.setItem('docs_site_lang', newLang);

    // Check if we're on HomePage (reuse the check from above)

    if (isHomePage) {
      // On HomePage: just update localStorage, don't navigate
      // HomePage will re-render and pick up the new language from localStorage
      window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang: newLang } }));
      return;
    }

    // On DocsPage: navigate to same document in new language
    const currentSlug = hashMatch ? hashMatch[1] : (pathMatch ? pathMatch[1] : null);

    // Try to find the same document in new language, fallback to overview
    let targetSlug = currentSlug;
    if (!currentSlug) {
      // If no current slug, get main document for new language
      const mainSlug = await getMainDocumentSlug(newLang);
      targetSlug = mainSlug || 'overview';
    }
    // If currentSlug exists, try to use it (assume same slug exists in new language)

    navigate(`/${newLang}/${targetSlug}${location.hash}`, { replace: true });
  }

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center justify-between px-4 md:px-6">
        <div className="flex items-center gap-4">
          {showSidebar && (
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={onMenuClick}
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? (
                <X className="h-5 w-5" />
              ) : (
                <Menu className="h-5 w-5" />
              )}
            </Button>
          )}

          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-foreground">
              <svg
                className="h-4 w-4 text-background"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M4 6h16M4 12h12M4 18h8" />
              </svg>
            </div>
            <span className="font-semibold text-foreground">
              Trading Research Assistant
            </span>
          </Link>
        </div>

        <div className="flex items-center gap-2">
          <SearchModal />

          {languageOptions.length > 1 && (
            <Dropdown
              value={effectiveCurrentLang}
              options={languageOptions}
              onChange={handleLanguageChange}
            />
          )}

          <a
            href="https://github.com/AmaLS367/Trading-research-assistant"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
            aria-label="GitHub"
          >
            <Github className="h-5 w-5" />
          </a>

          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
