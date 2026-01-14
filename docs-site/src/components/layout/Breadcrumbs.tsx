import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { useDocs } from '@/lib/docs-context';

export default function Breadcrumbs() {
  const location = useLocation();
  const { currentLang, navigation } = useDocs();

  const pathParts = location.pathname
    .replace(`/${currentLang}/`, '')
    .split('/')
    .filter(Boolean);

  if (pathParts.length === 0) return null;

  function getTitle(slug: string): string {
    for (const group of navigation) {
      for (const item of group.items) {
        if (item.slug === slug || item.slug.endsWith(slug)) {
          return item.title;
        }
      }
    }
    return slug
      .split('-')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  const breadcrumbs = pathParts.map((part, index) => {
    const slug = pathParts.slice(0, index + 1).join('/');
    return {
      label: getTitle(part),
      path: `/${currentLang}/${slug}`,
      isLast: index === pathParts.length - 1,
    };
  });

  return (
    <nav aria-label="Breadcrumb" className="mb-4">
      <ol className="flex flex-wrap items-center gap-1 text-sm">
        <li>
          <Link
            to={`/${currentLang}`}
            className="flex items-center text-muted-foreground hover:text-foreground transition-colors"
          >
            <Home className="h-4 w-4" />
          </Link>
        </li>

        {breadcrumbs.map((crumb) => (
          <li key={crumb.path} className="flex items-center gap-1">
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
            {crumb.isLast ? (
              <span className="font-medium text-foreground">{crumb.label}</span>
            ) : (
              <Link
                to={crumb.path}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                {crumb.label}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
