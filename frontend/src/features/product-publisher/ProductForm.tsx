import { useEffect, useState } from "react";
import { Save, Send, RotateCcw } from "lucide-react";
import { toast } from "sonner";

import { RankMathFields } from "@/features/_shared/RankMathFields";
import { MediaPicker } from "@/features/_shared/MediaPicker";
import { TextField } from "@/components/inputs/TextField";
import { TextArea } from "@/components/inputs/TextArea";
import { SelectField } from "@/components/inputs/SelectField";
import { connectionApi } from "@/services/connectionApi";
import { productApi, productTaxonomyApi } from "@/services/productApi";
import type { Connection } from "@/types/connection";
import type { MediaItem } from "@/types/media";
import type {
  Backorders,
  CatalogVisibility,
  ProductPublishResponse,
  ProductStatus,
  StockStatus,
  TaxStatus,
  WCCategoryItem,
  WCTagItem,
} from "@/types/product";
import type { RankMathMeta } from "@/types/content";
import { ApiError } from "@/types/errors";

interface FormState {
  connectionId: number | null;
  // Basic
  name: string;
  slug: string;
  status: ProductStatus;
  featured: boolean;
  catalogVisibility: CatalogVisibility;
  description: string;
  shortDescription: string;
  sku: string;
  // Pricing
  regularPrice: string;
  salePrice: string;
  dateOnSaleFrom: string;
  dateOnSaleTo: string;
  taxStatus: TaxStatus;
  taxClass: string;
  // Inventory
  manageStock: boolean;
  stockQuantity: string;
  stockStatus: StockStatus;
  backorders: Backorders;
  lowStockAmount: string;
  soldIndividually: boolean;
  // Shipping
  weight: string;
  dimensionsLength: string;
  dimensionsWidth: string;
  dimensionsHeight: string;
  shippingClass: string;
  // Organization
  categoryIds: number[];
  tagIds: number[];
  // Media
  featuredImage: MediaItem | null;
  // Related
  upsellIds: string;
  crossSellIds: string;
  // Advanced
  reviewsAllowed: boolean;
  purchaseNote: string;
  menuOrder: number;
  // Rank Math
  rankMath: RankMathMeta;
}

const INITIAL: FormState = {
  connectionId: null,
  name: "",
  slug: "",
  status: "draft",
  featured: false,
  catalogVisibility: "visible",
  description: "",
  shortDescription: "",
  sku: "",
  regularPrice: "",
  salePrice: "",
  dateOnSaleFrom: "",
  dateOnSaleTo: "",
  taxStatus: "taxable",
  taxClass: "",
  manageStock: false,
  stockQuantity: "",
  stockStatus: "instock",
  backorders: "no",
  lowStockAmount: "",
  soldIndividually: false,
  weight: "",
  dimensionsLength: "",
  dimensionsWidth: "",
  dimensionsHeight: "",
  shippingClass: "",
  categoryIds: [],
  tagIds: [],
  featuredImage: null,
  upsellIds: "",
  crossSellIds: "",
  reviewsAllowed: true,
  purchaseNote: "",
  menuOrder: 0,
  rankMath: {},
};

const STATUS_OPTIONS = [
  { value: "draft", label: "Draft" },
  { value: "publish", label: "Publish" },
  { value: "pending", label: "Pending review" },
  { value: "private", label: "Private" },
];

const VISIBILITY_OPTIONS = [
  { value: "visible", label: "Shop and search results" },
  { value: "catalog", label: "Shop only" },
  { value: "search", label: "Search results only" },
  { value: "hidden", label: "Hidden" },
];

const STOCK_STATUS_OPTIONS = [
  { value: "instock", label: "In stock" },
  { value: "outofstock", label: "Out of stock" },
  { value: "onbackorder", label: "On backorder" },
];

const BACKORDERS_OPTIONS = [
  { value: "no", label: "Do not allow" },
  { value: "notify", label: "Allow, but notify customer" },
  { value: "yes", label: "Allow" },
];

const TAX_STATUS_OPTIONS = [
  { value: "taxable", label: "Taxable" },
  { value: "shipping", label: "Shipping only" },
  { value: "none", label: "None" },
];

function parseIdList(input: string): number[] {
  return input
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .map((s) => Number(s))
    .filter((n) => Number.isFinite(n) && n > 0);
}

export function ProductForm(): JSX.Element {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [categories, setCategories] = useState<WCCategoryItem[]>([]);
  const [tags, setTags] = useState<WCTagItem[]>([]);
  const [form, setForm] = useState<FormState>(INITIAL);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<ProductPublishResponse | null>(null);

  // Load connections
  useEffect(() => {
    void (async () => {
      try {
        const res = await connectionApi.list();
        setConnections(res.connections);
        const first = res.connections[0];
        if (first) {
          setForm((f) => ({ ...f, connectionId: first.id }));
        }
      } catch {
        toast.error("Failed to load connections.");
      }
    })();
  }, []);

  // Load product taxonomies on connection change
  useEffect(() => {
    if (!form.connectionId) return;
    void (async () => {
      try {
        const [cats, tgs] = await Promise.all([
          productTaxonomyApi.listCategories(form.connectionId as number),
          productTaxonomyApi.listTags(form.connectionId as number),
        ]);
        setCategories(cats.items);
        setTags(tgs.items);
      } catch {
        setCategories([]);
        setTags([]);
      }
    })();
  }, [form.connectionId]);

  const update = <K extends keyof FormState>(key: K, value: FormState[K]): void => {
    setForm((f) => ({ ...f, [key]: value }));
  };

  const reset = (): void => {
    setForm({ ...INITIAL, connectionId: form.connectionId });
    setResult(null);
  };

  const validate = (): string | null => {
    if (!form.connectionId) return "Select a connection.";
    if (!form.name.trim()) return "Product name is required.";
    if (
      form.regularPrice &&
      Number.isNaN(Number(form.regularPrice))
    ) {
      return "Regular price must be a number.";
    }
    if (form.salePrice && Number.isNaN(Number(form.salePrice))) {
      return "Sale price must be a number.";
    }
    return null;
  };

  const submit = async (statusOverride?: ProductStatus): Promise<void> => {
    const status = statusOverride ?? form.status;
    if (status !== form.status) update("status", status);
    const err = validate();
    if (err) {
      toast.error(err);
      return;
    }
    setSaving(true);
    setResult(null);
    try {
      const images = form.featuredImage
        ? [
            {
              id: form.featuredImage.wp_media_id ?? undefined,
              alt: form.featuredImage.alt_text ?? undefined,
            },
          ]
        : undefined;

      const payload = {
        connection_id: form.connectionId as number,
        name: form.name.trim(),
        slug: form.slug.trim() || undefined,
        status,
        featured: form.featured,
        catalog_visibility: form.catalogVisibility,
        description: form.description,
        short_description: form.shortDescription,
        sku: form.sku.trim() || undefined,
        regular_price: form.regularPrice,
        sale_price: form.salePrice,
        date_on_sale_from: form.dateOnSaleFrom || undefined,
        date_on_sale_to: form.dateOnSaleTo || undefined,
        tax_status: form.taxStatus,
        tax_class: form.taxClass,
        manage_stock: form.manageStock,
        stock_quantity: form.stockQuantity
          ? Number(form.stockQuantity)
          : undefined,
        stock_status: form.stockStatus,
        backorders: form.backorders,
        low_stock_amount: form.lowStockAmount
          ? Number(form.lowStockAmount)
          : undefined,
        sold_individually: form.soldIndividually,
        weight: form.weight,
        dimensions: {
          length: form.dimensionsLength,
          width: form.dimensionsWidth,
          height: form.dimensionsHeight,
        },
        shipping_class: form.shippingClass,
        category_ids: form.categoryIds,
        tag_ids: form.tagIds,
        images,
        upsell_ids: parseIdList(form.upsellIds),
        cross_sell_ids: parseIdList(form.crossSellIds),
        reviews_allowed: form.reviewsAllowed,
        purchase_note: form.purchaseNote,
        menu_order: form.menuOrder,
        rank_math:
          Object.keys(form.rankMath).length > 0 ? form.rankMath : undefined,
      };

      const res = await productApi.create(payload);
      setResult(res);
      if (res.partial) {
        toast.warning(`Saved with warnings. ${res.message}`);
      } else {
        toast.success(res.message || "Product saved.");
      }
    } catch (e) {
      if (e instanceof ApiError) {
        toast.error(`Failed: ${e.message}`);
      } else {
        toast.error("Failed to save product.");
      }
    } finally {
      setSaving(false);
    }
  };

  const disabled = saving;

  return (
    <div className="space-y-6">
      {/* Actions bar */}
      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-surface-border bg-white px-4 py-3">
        <button
          type="button"
          onClick={() => void submit("draft")}
          disabled={disabled}
          className="inline-flex items-center gap-1.5 rounded border border-surface-border px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-surface-muted disabled:opacity-50"
        >
          <Save className="h-4 w-4" />
          Save Draft
        </button>
        <button
          type="button"
          onClick={() => void submit("publish")}
          disabled={disabled}
          className="inline-flex items-center gap-1.5 rounded bg-brand px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
          Publish
        </button>
        <button
          type="button"
          onClick={reset}
          disabled={disabled}
          className="ml-auto inline-flex items-center gap-1.5 rounded border border-surface-border px-3 py-1.5 text-sm font-medium text-slate-500 hover:bg-surface-muted disabled:opacity-50"
        >
          <RotateCcw className="h-4 w-4" />
          Reset
        </button>
      </div>

      {connections.length === 0 ? (
        <div className="rounded-lg border border-warning bg-warning-light/30 p-4 text-sm text-warning">
          Add a connection with WooCommerce REST keys first.
        </div>
      ) : null}

      {/* Basic */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">
          Basic Information
        </h2>

        {connections.length > 1 ? (
          <SelectField
            label="Connection"
            value={form.connectionId?.toString() ?? ""}
            onChange={(v) => update("connectionId", Number(v))}
            options={connections.map((c) => ({
              value: c.id.toString(),
              label: c.label,
            }))}
          />
        ) : null}

        <TextField
          label="Product name"
          value={form.name}
          onChange={(v) => update("name", v)}
          placeholder="Example: Herbal Hair Oil"
          required
          maxLength={500}
        />

        <TextField
          label="Slug"
          value={form.slug}
          onChange={(v) => update("slug", v)}
          placeholder="Example: herbal-hair-oil"
          help="URL-friendly identifier. Leave empty to let WooCommerce generate one."
          maxLength={300}
        />

        <TextField
          label="SKU"
          value={form.sku}
          onChange={(v) => update("sku", v)}
          placeholder="Example: HHO-001"
          help="Unique identifier. Must not conflict with existing products."
          maxLength={100}
        />

        <TextArea
          label="Short description"
          value={form.shortDescription}
          onChange={(v) => update("shortDescription", v)}
          placeholder="Example: Daily care hair oil."
          help="Shown near the price on the product page."
          rows={2}
        />

        <TextArea
          label="Full description"
          value={form.description}
          onChange={(v) => update("description", v)}
          placeholder="<p>Natural herbal hair oil for daily care.</p>"
          help="HTML allowed. Sanitized by WooCommerce on save."
          rows={6}
        />

        <SelectField
          label="Status"
          value={form.status}
          onChange={(v) => update("status", v as ProductStatus)}
          options={STATUS_OPTIONS}
        />

        <SelectField
          label="Catalog visibility"
          value={form.catalogVisibility}
          onChange={(v) => update("catalogVisibility", v as CatalogVisibility)}
          options={VISIBILITY_OPTIONS}
        />

        <label className="mb-4 flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={form.featured}
            onChange={(e) => update("featured", e.target.checked)}
            className="h-4 w-4 rounded border-surface-border"
          />
          Mark as featured product
        </label>
      </section>

      {/* Pricing */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">Pricing</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <TextField
            label="Regular price"
            value={form.regularPrice}
            onChange={(v) => update("regularPrice", v)}
            placeholder="Example: 499.00"
            help="Numeric value. Store currency is applied automatically."
          />
          <TextField
            label="Sale price"
            value={form.salePrice}
            onChange={(v) => update("salePrice", v)}
            placeholder="Example: 399.00"
            help="Leave empty if not on sale."
          />
          <TextField
            label="Sale starts"
            value={form.dateOnSaleFrom}
            onChange={(v) => update("dateOnSaleFrom", v)}
            placeholder="Example: 2026-11-01"
            help="Optional. ISO date."
          />
          <TextField
            label="Sale ends"
            value={form.dateOnSaleTo}
            onChange={(v) => update("dateOnSaleTo", v)}
            placeholder="Example: 2026-11-30"
            help="Optional. ISO date."
          />
        </div>
        <SelectField
          label="Tax status"
          value={form.taxStatus}
          onChange={(v) => update("taxStatus", v as TaxStatus)}
          options={TAX_STATUS_OPTIONS}
        />
        <TextField
          label="Tax class"
          value={form.taxClass}
          onChange={(v) => update("taxClass", v)}
          placeholder="Example: reduced-rate"
          help="Optional. Matches a tax class defined in WooCommerce."
        />
      </section>

      {/* Inventory */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">
          Inventory
        </h2>
        <label className="mb-4 flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={form.manageStock}
            onChange={(e) => update("manageStock", e.target.checked)}
            className="h-4 w-4 rounded border-surface-border"
          />
          Manage stock for this product
        </label>
        {form.manageStock ? (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <TextField
              label="Stock quantity"
              value={form.stockQuantity}
              onChange={(v) => update("stockQuantity", v)}
              placeholder="Example: 50"
              type="number"
            />
            <TextField
              label="Low stock threshold"
              value={form.lowStockAmount}
              onChange={(v) => update("lowStockAmount", v)}
              placeholder="Example: 5"
              type="number"
            />
          </div>
        ) : null}
        <SelectField
          label="Stock status"
          value={form.stockStatus}
          onChange={(v) => update("stockStatus", v as StockStatus)}
          options={STOCK_STATUS_OPTIONS}
        />
        <SelectField
          label="Backorders"
          value={form.backorders}
          onChange={(v) => update("backorders", v as Backorders)}
          options={BACKORDERS_OPTIONS}
        />
        <label className="mb-4 flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={form.soldIndividually}
            onChange={(e) => update("soldIndividually", e.target.checked)}
            className="h-4 w-4 rounded border-surface-border"
          />
          Sold individually
        </label>
      </section>

      {/* Shipping */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">Shipping</h2>
        <TextField
          label="Weight"
          value={form.weight}
          onChange={(v) => update("weight", v)}
          placeholder="Example: 0.5"
          help="In the store's configured weight unit."
        />
        <div className="grid grid-cols-3 gap-3">
          <TextField
            label="Length"
            value={form.dimensionsLength}
            onChange={(v) => update("dimensionsLength", v)}
            placeholder="10"
          />
          <TextField
            label="Width"
            value={form.dimensionsWidth}
            onChange={(v) => update("dimensionsWidth", v)}
            placeholder="5"
          />
          <TextField
            label="Height"
            value={form.dimensionsHeight}
            onChange={(v) => update("dimensionsHeight", v)}
            placeholder="5"
          />
        </div>
        <TextField
          label="Shipping class"
          value={form.shippingClass}
          onChange={(v) => update("shippingClass", v)}
          placeholder="Example: fragile"
          help="Optional. Matches a shipping class defined in WooCommerce."
        />
      </section>

      {/* Media */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">
          Featured Image
        </h2>
        {form.connectionId !== null ? (
          <MediaPicker
            connectionId={form.connectionId}
            value={form.featuredImage}
            onChange={(m) => update("featuredImage", m)}
          />
        ) : (
          <p className="text-xs text-slate-500">Select a connection first.</p>
        )}
      </section>

      {/* Organization */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">
          Organization
        </h2>

        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Categories
          </label>
          {categories.length === 0 ? (
            <p className="text-xs text-slate-500">
              No product categories yet on this store.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {categories.map((c) => (
                <label
                  key={c.id}
                  className={`inline-flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${
                    form.categoryIds.includes(c.id)
                      ? "border-brand bg-brand-light text-brand-dark"
                      : "border-surface-border bg-white text-slate-600 hover:bg-surface-muted"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={form.categoryIds.includes(c.id)}
                    onChange={(e) => {
                      const next = e.target.checked
                        ? [...form.categoryIds, c.id]
                        : form.categoryIds.filter((x) => x !== c.id);
                      update("categoryIds", next);
                    }}
                    className="hidden"
                  />
                  {c.name} ({c.count})
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Tags
          </label>
          {tags.length === 0 ? (
            <p className="text-xs text-slate-500">
              No product tags yet on this store.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {tags.map((t) => (
                <label
                  key={t.id}
                  className={`inline-flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${
                    form.tagIds.includes(t.id)
                      ? "border-brand bg-brand-light text-brand-dark"
                      : "border-surface-border bg-white text-slate-600 hover:bg-surface-muted"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={form.tagIds.includes(t.id)}
                    onChange={(e) => {
                      const next = e.target.checked
                        ? [...form.tagIds, t.id]
                        : form.tagIds.filter((x) => x !== t.id);
                      update("tagIds", next);
                    }}
                    className="hidden"
                  />
                  {t.name} ({t.count})
                </label>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Related */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">
          Related Products
        </h2>
        <TextField
          label="Upsells"
          value={form.upsellIds}
          onChange={(v) => update("upsellIds", v)}
          placeholder="Example: 501, 502"
          help="Comma-separated product IDs recommended as upgrades."
        />
        <TextField
          label="Cross-sells"
          value={form.crossSellIds}
          onChange={(v) => update("crossSellIds", v)}
          placeholder="Example: 601, 602"
          help="Comma-separated product IDs shown in cart."
        />
      </section>

      {/* Advanced */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">Advanced</h2>
        <label className="mb-4 flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={form.reviewsAllowed}
            onChange={(e) => update("reviewsAllowed", e.target.checked)}
            className="h-4 w-4 rounded border-surface-border"
          />
          Allow customer reviews
        </label>
        <TextArea
          label="Purchase note"
          value={form.purchaseNote}
          onChange={(v) => update("purchaseNote", v)}
          placeholder="Example: Thank you for your order. We will ship within 2 business days."
          help="Shown in the order confirmation email."
          rows={3}
        />
        <TextField
          label="Menu order"
          value={form.menuOrder.toString()}
          onChange={(v) => update("menuOrder", Number(v) || 0)}
          placeholder="0"
          help="Custom ordering position in product listings."
          type="number"
        />
      </section>

      {/* Rank Math */}
      <section className="rounded-lg border border-surface-border bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-slate-800">
          Rank Math SEO
        </h2>
        <RankMathFields
          value={form.rankMath}
          onChange={(v) => update("rankMath", v)}
          disabled={disabled}
        />
      </section>

      {/* Result */}
      {result ? (
        <section
          className={`rounded-lg border p-5 ${
            result.partial
              ? "border-warning bg-warning-light/30"
              : "border-success bg-success-light/30"
          }`}
        >
          <h3 className="mb-2 text-sm font-semibold">
            {result.partial ? "Saved with warnings" : "Saved successfully"}
          </h3>
          <p className="mb-2 text-sm text-slate-700">{result.message}</p>
          {result.permalink ? (
            <p className="text-xs">
              Permalink:{" "}
              <a
                href={result.permalink}
                target="_blank"
                rel="noreferrer"
                className="font-mono text-brand underline"
              >
                {result.permalink}
              </a>
            </p>
          ) : null}
          {result.warnings.length > 0 ? (
            <ul className="mt-2 ml-4 list-disc space-y-0.5 text-xs text-warning">
              {result.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}