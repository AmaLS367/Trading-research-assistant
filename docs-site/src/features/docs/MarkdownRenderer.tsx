import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import { Check, Copy } from 'lucide-react';
import { useState } from 'react';
import { copyToClipboard } from '@/lib/utils';
import MermaidBlock from './MermaidBlock';

interface MarkdownRendererProps {
  content: string;
  currentLang: string;
  currentSlug: string;
}

export default function MarkdownRenderer({
  content,
  currentLang,
  currentSlug,
}: MarkdownRendererProps) {
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

  return (
    <div className="prose prose-slate max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, [rehypeSanitize, sanitizeSchema]]}
        components={{
          code: CodeBlock,
          a: (props) => LinkComponent(props, currentLang, currentSlug),
          img: ImageComponent,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
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
