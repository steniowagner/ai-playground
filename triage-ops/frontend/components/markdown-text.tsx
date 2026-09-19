import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MarkdownTextProps = {
  children: string;
  className?: string;
};

export function MarkdownText({ children, className }: MarkdownTextProps) {
  const classes = ["markdown-content", className].filter(Boolean).join(" ");

  return (
    <div className={classes}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}
