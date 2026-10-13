import { ContentForm } from "@/features/_shared/ContentForm";

export function BlogPublisherPage(): JSX.Element {
  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">
        Blog Publisher
      </h1>
      <ContentForm kind="post" />
    </div>
  );
}