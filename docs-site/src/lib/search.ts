export interface SearchResult {
  title: string;
  slug: string;
  excerpt: string;
  score: number;
}

export interface SearchIndex {
  entries: SearchEntry[];
}

interface SearchEntry {
  title: string;
  slug: string;
  content: string;
  headings: string[];
}

export function createSearchIndex(
  pages: Array<{ title: string; slug: string; content: string }>
): SearchIndex {
  const entries: SearchEntry[] = pages.map((page) => {
    const headings = extractHeadings(page.content);
    return {
      title: page.title,
      slug: page.slug,
      content: stripMarkdown(page.content).toLowerCase(),
      headings: headings.map((h) => h.toLowerCase()),
    };
  });

  return { entries };
}

function extractHeadings(markdown: string): string[] {
  const regex = /^#{1,6}\s+(.+)$/gm;
  const headings: string[] = [];
  let match;

  while ((match = regex.exec(markdown)) !== null) {
    headings.push(match[1].trim());
  }

  return headings;
}

function stripMarkdown(markdown: string): string {
  return markdown
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`[^`]+`/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[#*_~`>]/g, '')
    .replace(/\n+/g, ' ')
    .trim();
}

export function search(
  index: SearchIndex,
  query: string,
  limit: number = 10
): SearchResult[] {
  if (!query.trim()) return [];

  const queryLower = query.toLowerCase();
  const queryTerms = queryLower.split(/\s+/).filter(Boolean);

  const results: SearchResult[] = [];

  for (const entry of index.entries) {
    let score = 0;

    if (entry.title.toLowerCase().includes(queryLower)) {
      score += 10;
    }

    for (const heading of entry.headings) {
      if (heading.includes(queryLower)) {
        score += 5;
      }
    }

    for (const term of queryTerms) {
      if (entry.content.includes(term)) {
        score += 1;

        const regex = new RegExp(term, 'gi');
        const matches = entry.content.match(regex);
        if (matches) {
          score += Math.min(matches.length, 5);
        }
      }
    }

    if (score > 0) {
      const excerpt = createExcerpt(entry.content, queryLower);
      results.push({
        title: entry.title,
        slug: entry.slug,
        excerpt,
        score,
      });
    }
  }

  return results
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}

function createExcerpt(content: string, query: string): string {
  const index = content.indexOf(query);

  if (index === -1) {
    return content.slice(0, 150) + '...';
  }

  const start = Math.max(0, index - 50);
  const end = Math.min(content.length, index + query.length + 100);

  let excerpt = content.slice(start, end);

  if (start > 0) excerpt = '...' + excerpt;
  if (end < content.length) excerpt = excerpt + '...';

  return excerpt;
}
