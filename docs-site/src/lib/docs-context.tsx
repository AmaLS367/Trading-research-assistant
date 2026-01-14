import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useCallback,
} from 'react';
import {
  DocsManifest,
  NavGroup,
  fetchManifest,
  fetchMarkdown,
  fetchNavConfig,
  buildNavigation,
  extractTitle,
} from './docs-manifest';

interface PageContent {
  markdown: string;
  title: string;
}

interface DocsContextType {
  isLoading: boolean;
  manifest: DocsManifest | null;
  languages: string[];
  defaultLanguage: string;
  navigation: NavGroup[];
  currentLang: string;
  setCurrentLang: (lang: string) => void;
  getPageContent: (slug: string, lang?: string) => Promise<PageContent | null>;
  getMainDocumentSlug: (lang?: string) => Promise<string | null>;
  pageCache: Map<string, PageContent>;
}

const DocsContext = createContext<DocsContextType | undefined>(undefined);

export function DocsProvider({ children }: { children: ReactNode }) {
  const [isLoading, setIsLoading] = useState(true);
  const [manifest, setManifest] = useState<DocsManifest | null>(null);
  const [currentLang, setCurrentLang] = useState('');
  const [navigation, setNavigation] = useState<NavGroup[]>([]);
  const [pageCache] = useState<Map<string, PageContent>>(new Map());

  const languages = manifest?.languages || [];
  const defaultLanguage = languages.includes('en') ? 'en' : languages[0] || '';

  useEffect(() => {
    async function loadManifest() {
      const data = await fetchManifest();
      setManifest(data);
      if (data?.languages.length) {
        const defaultLang = data.languages.includes('en')
          ? 'en'
          : data.languages[0];
        setCurrentLang(defaultLang);
      }
      setIsLoading(false);
    }

    loadManifest();
  }, []);

  useEffect(() => {
    async function loadNavigation() {
      if (!manifest || !currentLang) return;

      const allFiles = manifest.filesByLanguage[currentLang] || [];
      const nav = await buildNavigation(allFiles, currentLang);

      for (const group of nav) {
        for (const item of group.items) {
          const content = await fetchMarkdown(item.path);
          if (content) {
            const title = extractTitle(content);
            if (title) {
              item.title = title;
            }
          }
        }
      }

      setNavigation(nav);
    }

    loadNavigation();
  }, [manifest, currentLang]);

  const getPageContent = useCallback(
    async (slug: string, lang?: string): Promise<PageContent | null> => {
      const targetLang = lang || currentLang;
      const cacheKey = `${targetLang}/${slug}`;

      if (pageCache.has(cacheKey)) {
        return pageCache.get(cacheKey)!;
      }

      const filePath = `${targetLang}/${slug}.md`;
      const markdown = await fetchMarkdown(filePath);

      if (!markdown) {
        const indexPath = `${targetLang}/${slug}/index.md`;
        const indexMarkdown = await fetchMarkdown(indexPath);

        if (!indexMarkdown) return null;

        const content = {
          markdown: indexMarkdown,
          title: extractTitle(indexMarkdown) || slug,
        };
        pageCache.set(cacheKey, content);
        return content;
      }

      const content = {
        markdown,
        title: extractTitle(markdown) || slug,
      };
      pageCache.set(cacheKey, content);
      return content;
    },
    [currentLang, pageCache]
  );

  const getMainDocumentSlug = useCallback(async (lang?: string): Promise<string | null> => {
    const targetLang = lang || currentLang;
    if (!manifest || !targetLang) return null;

    const files = manifest.filesByLanguage[targetLang] || [];
    if (files.length === 0) return null;

    const overviewFile = files.find(f => f.endsWith('overview.md'));
    if (overviewFile) {
      const slug = overviewFile.replace(`${targetLang}/`, '').replace('.md', '');
      return slug;
    }

    const readmeFile = files.find(f => f.endsWith('README.md'));
    if (readmeFile) {
      const slug = readmeFile.replace(`${targetLang}/`, '').replace('.md', '');
      return slug;
    }

    const navConfig = await fetchNavConfig(targetLang);
    if (navConfig?.groups && navConfig.groups.length > 0) {
      const firstGroup = navConfig.groups[0];
      if (firstGroup.items && firstGroup.items.length > 0) {
        const firstItem = firstGroup.items[0];
        return firstItem.replace('.md', '');
      }
    }

    const sortedFiles = [...files].sort();
    if (sortedFiles.length > 0) {
      const firstFile = sortedFiles[0];
      const slug = firstFile.replace(`${targetLang}/`, '').replace('.md', '');
      return slug;
    }

    return null;
  }, [manifest, currentLang]);

  return (
    <DocsContext.Provider
      value={{
        isLoading,
        manifest,
        languages,
        defaultLanguage,
        navigation,
        currentLang,
        setCurrentLang,
        getPageContent,
        getMainDocumentSlug,
        pageCache,
      }}
    >
      {children}
    </DocsContext.Provider>
  );
}

export function useDocs() {
  const context = useContext(DocsContext);
  if (!context) {
    throw new Error('useDocs must be used within a DocsProvider');
  }
  return context;
}
