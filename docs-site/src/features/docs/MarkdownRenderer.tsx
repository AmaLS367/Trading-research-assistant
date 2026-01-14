import { useState } from 'react';
import { Check, Copy, Info, AlertTriangle } from 'lucide-react';
import { copyToClipboard, cn } from '@/lib/utils';
import MermaidBlock from './MermaidBlock';

interface MarkdownRendererProps {
  content: string;
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return <div className="prose">{renderMarkdown(content)}</div>;
}

function renderMarkdown(markdown: string): React.ReactNode[] {
  const lines = markdown.split('\n');
  const elements: React.ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith('```')) {
      const lang = line.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      const code = codeLines.join('\n');
      if (lang === 'mermaid') {
        elements.push(<MermaidBlock key={key++} code={code} />);
      } else {
        elements.push(<CodeBlock key={key++} code={code} lang={lang} />);
      }
      i++;
      continue;
    }

    if (line.startsWith('> **Note')) {
      elements.push(<Callout key={key++} type="note" content={line.slice(2)} />);
      i++;
      continue;
    }
    if (line.startsWith('> **Warning')) {
      elements.push(<Callout key={key++} type="warning" content={line.slice(2)} />);
      i++;
      continue;
    }

    if (line.startsWith('# ')) {
      elements.push(<h1 key={key++} className="text-3xl font-bold mt-8 mb-4 text-foreground">{parseInline(line.slice(2))}</h1>);
    } else if (line.startsWith('## ')) {
      elements.push(<h2 key={key++} className="text-2xl font-semibold mt-8 mb-3 text-foreground border-b border-border pb-2">{parseInline(line.slice(3))}</h2>);
    } else if (line.startsWith('### ')) {
      elements.push(<h3 key={key++} className="text-xl font-semibold mt-6 mb-2 text-foreground">{parseInline(line.slice(4))}</h3>);
    } else if (line.startsWith('#### ')) {
      elements.push(<h4 key={key++} className="text-lg font-medium mt-4 mb-2 text-foreground">{parseInline(line.slice(5))}</h4>);
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      const listItems: string[] = [line.slice(2)];
      while (i + 1 < lines.length && (lines[i + 1].startsWith('- ') || lines[i + 1].startsWith('* '))) {
        i++;
        listItems.push(lines[i].slice(2));
      }
      elements.push(
        <ul key={key++} className="list-disc list-inside my-4 space-y-1 text-foreground">
          {listItems.map((item, idx) => <li key={idx}>{parseInline(item)}</li>)}
        </ul>
      );
    } else if (/^\d+\.\s/.test(line)) {
      const listItems: string[] = [line.replace(/^\d+\.\s/, '')];
      while (i + 1 < lines.length && /^\d+\.\s/.test(lines[i + 1])) {
        i++;
        listItems.push(lines[i].replace(/^\d+\.\s/, ''));
      }
      elements.push(
        <ol key={key++} className="list-decimal list-inside my-4 space-y-1 text-foreground">
          {listItems.map((item, idx) => <li key={idx}>{parseInline(item)}</li>)}
        </ol>
      );
    } else if (line.startsWith('|')) {
      const tableLines: string[] = [line];
      while (i + 1 < lines.length && lines[i + 1].startsWith('|')) {
        i++;
        tableLines.push(lines[i]);
      }
      elements.push(<Table key={key++} lines={tableLines} />);
    } else if (line.trim() === '') {
      elements.push(<div key={key++} className="h-4" />);
    } else if (line.trim()) {
      elements.push(<p key={key++} className="my-3 text-foreground leading-7">{parseInline(line)}</p>);
    }
    i++;
  }

  return elements;
}

function parseInline(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining) {
    const codeMatch = remaining.match(/`([^`]+)`/);
    const boldMatch = remaining.match(/\*\*([^*]+)\*\*/);
    const linkMatch = remaining.match(/\[([^\]]+)\]\(([^)]+)\)/);

    const matches = [
      codeMatch ? { type: 'code', match: codeMatch, index: codeMatch.index! } : null,
      boldMatch ? { type: 'bold', match: boldMatch, index: boldMatch.index! } : null,
      linkMatch ? { type: 'link', match: linkMatch, index: linkMatch.index! } : null,
    ].filter(Boolean).sort((a, b) => a!.index - b!.index);

    if (matches.length === 0) {
      parts.push(remaining);
      break;
    }

    const first = matches[0]!;
    if (first.index > 0) {
      parts.push(remaining.slice(0, first.index));
    }

    if (first.type === 'code') {
      parts.push(<code key={key++} className="px-1.5 py-0.5 rounded bg-muted font-mono text-sm">{first.match[1]}</code>);
    } else if (first.type === 'bold') {
      parts.push(<strong key={key++} className="font-semibold">{first.match[1]}</strong>);
    } else if (first.type === 'link') {
      parts.push(<a key={key++} href={first.match[2]} className="text-primary hover:underline" target={first.match[2].startsWith('http') ? '_blank' : undefined}>{first.match[1]}</a>);
    }

    remaining = remaining.slice(first.index + first.match[0].length);
  }

  return parts.length === 1 ? parts[0] : parts;
}

function CodeBlock({ code, lang }: { code: string; lang: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await copyToClipboard(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="group relative my-4 rounded-lg border border-border bg-muted overflow-hidden">
      {lang && <div className="px-4 py-2 text-xs text-muted-foreground border-b border-border">{lang}</div>}
      <button onClick={handleCopy} className="absolute right-2 top-2 rounded p-1.5 text-muted-foreground hover:bg-accent opacity-0 group-hover:opacity-100 transition-opacity">
        {copied ? <Check className="h-4 w-4 text-success" /> : <Copy className="h-4 w-4" />}
      </button>
      <pre className="overflow-x-auto p-4 text-sm"><code className="font-mono">{code}</code></pre>
    </div>
  );
}

function Callout({ type, content }: { type: 'note' | 'warning'; content: string }) {
  const Icon = type === 'warning' ? AlertTriangle : Info;
  return (
    <div className={cn('my-4 flex gap-3 rounded-lg border p-4', type === 'warning' ? 'border-warning/50 bg-warning/10' : 'border-primary/20 bg-primary/5')}>
      <Icon className={cn('h-5 w-5 shrink-0', type === 'warning' ? 'text-warning' : 'text-primary')} />
      <div className="text-sm">{parseInline(content.replace(/^\*\*(Note|Warning)[:\s]*\*\*\s*/, ''))}</div>
    </div>
  );
}

function Table({ lines }: { lines: string[] }) {
  const rows = lines.filter(l => !l.match(/^\|[-:\s|]+\|$/)).map(l => l.split('|').slice(1, -1).map(c => c.trim()));
  const [header, ...body] = rows;
  return (
    <div className="my-4 overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead><tr className="border-b border-border">{header.map((cell, i) => <th key={i} className="px-4 py-2 text-left font-medium text-foreground">{cell}</th>)}</tr></thead>
        <tbody>{body.map((row, i) => <tr key={i} className="border-b border-border">{row.map((cell, j) => <td key={j} className="px-4 py-2 text-muted-foreground">{parseInline(cell)}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}
