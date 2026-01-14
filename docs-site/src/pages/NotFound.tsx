import { FileQuestion } from 'lucide-react';

interface NotFoundProps {
  message?: string;
}

export default function NotFound({ message }: NotFoundProps) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4 text-center">
      <FileQuestion className="h-16 w-16 text-muted-foreground" />
      <h1 className="mt-6 text-2xl font-bold text-foreground">No Documentation Found</h1>
      <p className="mt-2 max-w-md text-muted-foreground">{message || 'Please add markdown files to the docs/ directory.'}</p>
    </div>
  );
}
