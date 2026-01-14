import { Link } from 'react-router-dom';
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
  const { languages, currentLang, setCurrentLang } = useDocs();

  const languageOptions = languages.map((lang) => ({
    value: lang,
    label: getLanguageDisplayName(lang),
  }));

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
              value={currentLang}
              options={languageOptions}
              onChange={setCurrentLang}
            />
          )}

          <a
            href="https://github.com"
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
