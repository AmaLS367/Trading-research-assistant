import { NavLink, useLocation } from 'react-router-dom';
import { ChevronDown, FileText } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useDocs } from '@/lib/docs-context';
import { cn } from '@/lib/utils';
import { NavGroup } from '@/lib/docs-manifest';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { navigation, currentLang } = useDocs();
  const location = useLocation();
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  useEffect(() => {
    const currentPath = location.pathname.replace(`/${currentLang}/`, '');
    const newExpanded = new Set<string>();

    for (const group of navigation) {
      for (const item of group.items) {
        if (currentPath.startsWith(item.slug) || item.slug.startsWith(currentPath.split('/')[0])) {
          newExpanded.add(group.title);
          break;
        }
      }
    }

    setExpandedGroups((prev) => new Set([...prev, ...newExpanded]));
  }, [location.pathname, navigation, currentLang]);

  function toggleGroup(title: string) {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(title)) {
        next.delete(title);
      } else {
        next.add(title);
      }
      return next;
    });
  }

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={cn(
          'fixed left-0 top-16 z-40 h-[calc(100vh-4rem)] w-64 shrink-0 overflow-y-auto border-r border-border bg-background',
          'transition-transform duration-200 ease-in-out',
          'md:sticky md:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <nav className="p-4">
          {navigation.map((group) => (
            <SidebarGroup
              key={group.title}
              group={group}
              lang={currentLang}
              isExpanded={expandedGroups.has(group.title)}
              onToggle={() => toggleGroup(group.title)}
              onItemClick={onClose}
            />
          ))}
        </nav>
      </aside>
    </>
  );
}

interface SidebarGroupProps {
  group: NavGroup;
  lang: string;
  isExpanded: boolean;
  onToggle: () => void;
  onItemClick?: () => void;
}

function SidebarGroup({
  group,
  lang,
  isExpanded,
  onToggle,
  onItemClick,
}: SidebarGroupProps) {
  return (
    <div className="mb-4">
      <button
        onClick={onToggle}
        className={cn(
          'flex w-full items-center justify-between rounded-md px-2 py-1.5 text-sm font-medium',
          'text-foreground hover:bg-accent transition-colors'
        )}
      >
        <span>{group.title}</span>
        <ChevronDown
          className={cn(
            'h-4 w-4 text-muted-foreground transition-transform',
            isExpanded && 'rotate-180'
          )}
        />
      </button>

      {isExpanded && (
        <ul className="mt-1 space-y-1 animate-fade-in">
          {group.items.map((item) => (
            <li key={item.slug}>
              <NavLink
                to={`/${lang}/${item.slug}`}
                onClick={onItemClick}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors',
                    'hover:bg-accent',
                    isActive
                      ? 'bg-accent font-medium text-foreground'
                      : 'text-muted-foreground'
                  )
                }
              >
                <FileText className="h-4 w-4 shrink-0" />
                <span className="truncate">{item.title}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
