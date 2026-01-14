import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

interface MermaidBlockProps {
  code: string;
}

export default function MermaidBlock({ code }: MermaidBlockProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: document.documentElement.classList.contains('dark') ? 'dark' : 'default',
      securityLevel: 'loose',
    });

    async function render() {
      if (!containerRef.current) return;
      const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
      try {
        const { svg } = await mermaid.render(id, code);
        containerRef.current.innerHTML = svg;
      } catch (e) {
        containerRef.current.innerHTML = `<pre class="text-destructive text-sm">Mermaid error: ${e}</pre>`;
      }
    }

    render();
  }, [code]);

  return <div ref={containerRef} className="my-6 flex justify-center overflow-x-auto" />;
}
