export interface DocsManifest {
  languages: string[];
  filesByLanguage: Record<string, string[]>;
  generated: string;
}

export interface NavItem {
  title: string;
  path: string;
  slug: string;
  order?: number;
}

export interface NavGroup {
  title: string;
  items: NavItem[];
  order?: number;
}

export interface NavConfig {
  groups?: {
    title: string;
    items: string[];
    order?: number;
  }[];
  order?: string[];
}

export async function fetchManifest(): Promise<DocsManifest | null> {
  try {
    const response = await fetch('./docs-manifest.json');
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export async function fetchMarkdown(path: string): Promise<string | null> {
  try {
    const response = await fetch(`./docs/${path}`);
    if (!response.ok) return null;
    return await response.text();
  } catch {
    return null;
  }
}

export async function fetchNavConfig(lang: string): Promise<NavConfig | null> {
  try {
    const response = await fetch(`./docs/${lang}/_nav.json`);
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export function extractTitle(markdown: string): string | null {
  const match = markdown.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : null;
}

export function pathToSlug(filePath: string): string {
  return filePath
    .replace(/\.md$/, '')
    .replace(/\/index$/, '')
    .replace(/\\/g, '/');
}

export function slugToPath(slug: string, lang: string): string {
  return `${lang}/${slug}.md`;
}

export function fileNameToTitle(fileName: string): string {
  return fileName
    .replace(/\.md$/, '')
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function getGroupForFile(fileName: string): string {
  const baseName = fileName.replace('.md', '').toLowerCase();
  
  if (baseName === 'overview' || baseName === 'usage_guide' || baseName === 'usage-guide' || baseName === 'readme') {
    return 'Getting Started';
  }
  
  if (baseName === 'architecture' || baseName === 'import_rules' || baseName === 'import-rules') {
    return 'Reference';
  }
  
  if (baseName === 'safety_policy' || baseName === 'safety-policy') {
    return 'Policies';
  }
  
  if (baseName === 'troubleshooting') {
    return 'Troubleshooting';
  }
  
  return 'Other';
}

function getFileOrder(fileName: string): number {
  const baseName = fileName.replace('.md', '').toLowerCase();
  const orderMap: Record<string, number> = {
    'overview': 1,
    'readme': 2,
    'usage_guide': 3,
    'usage-guide': 4,
    'architecture': 5,
    'import_rules': 6,
    'import-rules': 7,
    'safety_policy': 8,
    'safety-policy': 9,
    'troubleshooting': 10,
  };
  
  return orderMap[baseName] || 999;
}

export function groupFilesByFolder(
  files: string[],
  lang: string
): NavGroup[] {
  const groups: Record<string, NavItem[]> = {};

  for (const file of files) {
    if (file.startsWith('_')) continue;

    const relativePath = file.replace(`${lang}/`, '');
    const parts = relativePath.split('/');
    const fileName = parts[parts.length - 1];

    let groupTitle: string;
    
    if (parts.length > 1) {
      const folder = parts[0];
      groupTitle = fileNameToTitle(folder);
    } else {
      groupTitle = getGroupForFile(fileName);
    }

    if (!groups[groupTitle]) {
      groups[groupTitle] = [];
    }

    groups[groupTitle].push({
      title: fileNameToTitle(fileName),
      path: file,
      slug: pathToSlug(relativePath),
    });
  }

  const groupOrder: Record<string, number> = {
    'Getting Started': 1,
    'Reference': 2,
    'Policies': 3,
    'Troubleshooting': 4,
    'Other': 999,
  };

  const result: NavGroup[] = [];

  Object.entries(groups)
    .sort(([a], [b]) => {
      const orderA = groupOrder[a] || 998;
      const orderB = groupOrder[b] || 998;
      if (orderA !== orderB) {
        return orderA - orderB;
      }
      return a.localeCompare(b);
    })
    .forEach(([title, items]) => {
      result.push({
        title,
        items: items.sort((a, b) => {
          const orderA = getFileOrder(a.path.split('/').pop() || '');
          const orderB = getFileOrder(b.path.split('/').pop() || '');
          if (orderA !== orderB) {
            return orderA - orderB;
          }
          return a.title.localeCompare(b.title);
        }),
      });
    });

  return result;
}

export async function buildNavigation(
  files: string[],
  lang: string
): Promise<NavGroup[]> {
  const langFiles = files.filter((f) => f.startsWith(`${lang}/`));
  const navConfig = await fetchNavConfig(lang);

  if (navConfig?.groups) {
    const result: NavGroup[] = [];

    for (const group of navConfig.groups) {
      const items: NavItem[] = [];

      for (const itemPath of group.items) {
        const fullPath = `${lang}/${itemPath}`;
        const matchingFile = langFiles.find((f) => f === fullPath || f === `${fullPath}.md`);

        if (matchingFile) {
          items.push({
            title: fileNameToTitle(itemPath.split('/').pop() || itemPath),
            path: matchingFile,
            slug: pathToSlug(matchingFile.replace(`${lang}/`, '')),
          });
        }
      }

      if (items.length > 0) {
        result.push({
          title: group.title,
          items,
          order: group.order,
        });
      }
    }

    return result;
  }

  return groupFilesByFolder(langFiles, lang);
}
