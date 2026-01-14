import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import { Check, Copy, Link as LinkIcon } from 'lucide-react';
import { useState } from 'react';
import { copyToClipboard, cn } from '@/lib/utils';
import MermaidBlock from './MermaidBlock';
import Toast from '@/components/ui/Toast';

interface MarkdownRendererProps {
  content: string;
  currentLang: string;
  currentSlug: string;
  onShowToast?: (message: string) => void;
}

export default function MarkdownRenderer({
  content,
  currentLang,
  currentSlug,
  onShowToast,
}: MarkdownRendererProps) {
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const isOverview = currentSlug.includes('overview');

  function showToast(message: string) {
    setToastMessage(message);
    if (onShowToast) {
      onShowToast(message);
    }
  }

  function generateId(text: string): string {
    return text
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim();
  }

  function extractHeroContent(markdown: string): {
    title: string;
    subtitle: string;
    badges: string;
    remainingContent: string;
  } | null {
    if (!isOverview) return null;

    const h1Match = markdown.match(/^#\s+(.+)$/m);
    if (!h1Match) return null;

    const title = h1Match[1].replace(/^📊\s*/, '').trim();
    const afterH1 = markdown.slice(h1Match.index! + h1Match[0].length).trim();

    const subtitleMatch = afterH1.match(/^\*\*(.+?)\*\*/);
    const subtitle = subtitleMatch ? subtitleMatch[1].trim() : '';

    const divMatch = afterH1.match(/<div[^>]*>([\s\S]*?)<\/div>/);
    let badges = '';
    if (divMatch) {
      badges = divMatch[1].trim();
    }

    let remainingStart = 0;
    const hrMatch = afterH1.match(/^---/m);
    if (hrMatch) {
      remainingStart = hrMatch.index! + hrMatch[0].length;
      const nextLine = afterH1.indexOf('\n', remainingStart);
      if (nextLine !== -1) {
        remainingStart = nextLine + 1;
      }
    } else {
      const doubleNewline = afterH1.indexOf('\n\n');
      if (doubleNewline !== -1) {
        remainingStart = doubleNewline + 2;
      } else {
        const singleNewline = afterH1.indexOf('\n');
        if (singleNewline !== -1) {
          remainingStart = singleNewline + 1;
        }
      }
    }

    const remainingContent = afterH1.slice(remainingStart).trim();

    return { title, subtitle, badges, remainingContent };
  }

  const heroContent = extractHeroContent(content);
  const renderContent = heroContent ? heroContent.remainingContent : content;

  const sanitizeSchema: any = {
    tagNames: [
      'details',
      'summary',
      'div',
      'span',
      'br',
      'kbd',
      'img',
      'a',
      'p',
      'h1',
      'h2',
      'h3',
      'h4',
      'h5',
      'h6',
      'ul',
      'ol',
      'li',
      'blockquote',
      'code',
      'pre',
      'strong',
      'em',
      'table',
      'thead',
      'tbody',
      'tr',
      'th',
      'td',
      'hr',
    ],
    attributes: {
      div: ['align', 'className'],
      details: ['open', 'className'],
      summary: ['className'],
      img: ['src', 'alt', 'className'],
      a: ['href', 'title', 'target', 'rel', 'className'],
      span: ['className'],
      kbd: ['className'],
      '*': ['className'],
    },
  };

  async function handleAnchorClick(text: string, e: React.MouseEvent) {
    e.preventDefault();
    const id = generateId(text);
    const url = `${window.location.origin}${window.location.pathname}#${id}`;
    try {
      await navigator.clipboard.writeText(url);
      showToast('Link copied');
    } catch (err) {
      console.error('Failed to copy link:', err);
    }
  }

  function HeadingComponent(
    props: React.HTMLAttributes<HTMLHeadingElement>,
    level: 2 | 3
  ) {
    const { children, className, ...rest } = props;
    const text = String(children);
    const id = generateId(text);

    return (
      <div className="group relative flex items-center gap-2">
        <button
          onClick={(e) => handleAnchorClick(text, e)}
          className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground shrink-0"
          aria-label="Copy link to heading"
        >
          <LinkIcon className="h-4 w-4" />
        </button>
        {level === 2 ? (
          <h2
            {...rest}
            id={id}
            className={cn(
              className,
              'scroll-mt-20 text-2xl font-semibold mt-12 mb-4 text-foreground border-b border-border pb-2 flex-1'
            )}
          >
            {children}
          </h2>
        ) : (
          <h3
            {...rest}
            id={id}
            className={cn(
              className,
              'scroll-mt-20 text-xl font-semibold mt-8 mb-3 text-foreground flex-1'
            )}
          >
            {children}
          </h3>
        )}
      </div>
    );
  }

  return (
    <>
      {heroContent && (
        <div className="mb-12 pb-8 border-b border-border">
          <h1 className="text-4xl font-bold mb-4 text-foreground">
            {heroContent.title}
          </h1>
          {heroContent.subtitle && (
            <p className="text-xl text-muted-foreground mb-6">
              {heroContent.subtitle}
            </p>
          )}
          {heroContent.badges && (
            <div
              className="flex flex-wrap gap-2 mb-6"
              dangerouslySetInnerHTML={{ __html: heroContent.badges }}
            />
          )}
        </div>
      )}
      <div className="prose prose-slate max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeRaw, [rehypeSanitize, sanitizeSchema]]}
          components={{
            code: CodeBlock,
            a: (props) => LinkComponent(props, currentLang, currentSlug),
            img: ImageComponent,
            h2: (props) => HeadingComponent(props, 2),
            h3: (props) => HeadingComponent(props, 3),
          }}
        >
          {renderContent}
        </ReactMarkdown>
      </div>
      {toastMessage && (
        <Toast
          message={toastMessage}
          onClose={() => setToastMessage(null)}
        />
      )}
    </>
  );
}

function CodeBlock({
  children,
  className,
}: {
  children?: React.ReactNode;
  className?: string;
  [key: string]: any;
}) {
  const match = /language-(\w+)/.exec(className || '');
  const lang = match ? match[1] : '';
  const code = String(children).replace(/\n$/, '');

  if (lang === 'mermaid') {
    return <MermaidBlock code={code} />;
  }

  return <CodeBlockWithCopy code={code} lang={lang} />;
}

function CodeBlockWithCopy({ code, lang }: { code: string; lang: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await copyToClipboard(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="group relative my-4 rounded-lg border border-border bg-muted overflow-hidden">
      {lang && (
        <div className="px-4 py-2 text-xs text-muted-foreground border-b border-border">
          {lang}
        </div>
      )}
      <button
        onClick={handleCopy}
        className="absolute right-2 top-2 rounded p-1.5 text-muted-foreground hover:bg-accent opacity-0 group-hover:opacity-100 transition-opacity"
      >
        {copied ? (
          <Check className="h-4 w-4 text-success" />
        ) : (
          <Copy className="h-4 w-4" />
        )}
      </button>
      <pre className="overflow-x-auto p-4 text-sm">
        <code className="font-mono">{code}</code>
      </pre>
    </div>
  );
}

function normalizePath(path: string): string {
  const segments = path.split('/').filter((s) => s !== '');
  const result: string[] = [];

  for (const segment of segments) {
    if (segment === '.') {
      continue;
    } else if (segment === '..') {
      result.pop();
    } else {
      result.push(segment);
    }
  }

  return result.join('/');
}

function resolveInternalLink(
  href: string,
  currentLang: string,
  currentSlug: string
): string | null {
  if (!href || href.startsWith('http://') || href.startsWith('https://')) {
    return null;
  }

  if (href.startsWith('#')) {
    return href;
  }

  if (!href.includes('.md')) {
    return null;
  }

  let anchor = '';
  if (href.includes('#')) {
    const parts = href.split('#');
    href = parts[0];
    anchor = '#' + parts.slice(1).join('#');
  }

  let targetLang = currentLang;
  let targetPath = href;

  if (href.startsWith('./')) {
    const currentDir = currentSlug.split('/').slice(0, -1).join('/');
    targetPath = normalizePath(`${currentDir}/${href.slice(2)}`);
  } else if (href.startsWith('../')) {
    const currentDir = currentSlug.split('/').slice(0, -1).join('/');
    targetPath = normalizePath(`${currentDir}/../${href.slice(3)}`);
  } else {
    targetPath = normalizePath(href);
  }

  const langMatch = targetPath.match(/^(en|ru|es|de|fr|ja|ko|zh)(?:\/|$)/);
  if (langMatch) {
    targetLang = langMatch[1];
    targetPath = targetPath.slice(targetLang.length + 1);
  }

  if (targetPath.endsWith('.md')) {
    targetPath = targetPath.slice(0, -3);
  }

  if (targetPath.endsWith('/index')) {
    targetPath = targetPath.slice(0, -6);
  }

  if (targetPath.endsWith('/')) {
    targetPath = targetPath.slice(0, -1);
  }

  return `/${targetLang}/${targetPath}${anchor}`;
}

function LinkComponent(
  props: React.AnchorHTMLAttributes<HTMLAnchorElement>,
  currentLang: string,
  currentSlug: string
) {
  const { href, children, ...rest } = props;

  if (!href) {
    return <a {...rest}>{children}</a>;
  }

  if (href.startsWith('http://') || href.startsWith('https://')) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-primary hover:underline"
        {...rest}
      >
        {children}
      </a>
    );
  }

  if (href.startsWith('#')) {
    return (
      <a href={href} className="text-primary hover:underline" {...rest}>
        {children}
      </a>
    );
  }

  const internalLink = resolveInternalLink(href, currentLang, currentSlug);
  if (internalLink) {
    return (
      <a
        href={internalLink}
        className="text-primary hover:underline"
        {...rest}
      >
        {children}
      </a>
    );
  }

  return (
    <a href={href} className="text-primary hover:underline" {...rest}>
      {children}
    </a>
  );
}

function ImageComponent(props: React.ImgHTMLAttributes<HTMLImageElement>) {
  const { src, alt, ...rest } = props;

  if (!src) {
    return null;
  }

  const isImageUrl =
    src.includes('shields.io') ||
    src.endsWith('.png') ||
    src.endsWith('.jpg') ||
    src.endsWith('.jpeg') ||
    src.endsWith('.gif') ||
    src.endsWith('.svg') ||
    src.endsWith('.webp');

  if (isImageUrl) {
    return (
      <img
        src={src}
        alt={alt || ''}
        className="max-w-full h-auto my-4"
        {...rest}
      />
    );
  }

  return (
    <a
      href={src}
      target="_blank"
      rel="noopener noreferrer"
      className="text-primary hover:underline"
    >
      {alt || src}
    </a>
  );
}
