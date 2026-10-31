import React from 'react';

/**
 * Minimal, dependency-free renderer for the subset of Markdown the advisor emits:
 * **bold**, bullet lists (-, *, •), numbered lists, headings (#) and paragraphs.
 * All text is rendered as React text nodes (no innerHTML), so it is XSS-safe.
 */
const renderInline = (text: string): React.ReactNode[] => {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith('**') && part.endsWith('**') && part.length > 4 ? (
      <strong key={i} className="font-semibold">
        {part.slice(2, -2)}
      </strong>
    ) : (
      <React.Fragment key={i}>{part.replace(/\*(?!\*)/g, '')}</React.Fragment>
    ),
  );
};

export const RichText: React.FC<{ text: string; className?: string }> = ({ text, className }) => {
  const lines = text.replace(/\r\n/g, '\n').split('\n');
  const blocks: React.ReactNode[] = [];
  let bullets: string[] = [];

  const flushBullets = () => {
    if (bullets.length === 0) return;
    const items = bullets;
    bullets = [];
    blocks.push(
      <ul key={`ul-${blocks.length}`} className="list-disc pl-5 space-y-1">
        {items.map((b, i) => (
          <li key={i}>{renderInline(b)}</li>
        ))}
      </ul>,
    );
  };

  lines.forEach((raw) => {
    const line = raw.trim();
    if (!line || /^[-*_]{3,}$/.test(line)) {
      flushBullets();
      return;
    }
    const bullet = line.match(/^(?:[-*•]|\d+[.)])\s+(.*)$/);
    if (bullet) {
      bullets.push(bullet[1]);
      return;
    }
    flushBullets();
    const heading = line.match(/^#{1,6}\s+(.*)$/);
    if (heading) {
      blocks.push(
        <p key={`h-${blocks.length}`} className="font-semibold">
          {renderInline(heading[1])}
        </p>,
      );
      return;
    }
    blocks.push(<p key={`p-${blocks.length}`}>{renderInline(line)}</p>);
  });
  flushBullets();

  return <div className={`space-y-2 ${className ?? ''}`}>{blocks}</div>;
};
