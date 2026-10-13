import { ProductForm } from "@/features/product-publisher/ProductForm";

export function ProductPublisherPage(): JSX.Element {
  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">
        Product Publisher
      </h1>
      <ProductForm />
    </div>
  );
}