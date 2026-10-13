import {
  BookOpen,
  ClipboardCheck,
  Crop,
  DatabaseBackup,
  FileText,
  History,
  Image as ImageIcon,
  LayoutDashboard,
  Link as LinkIcon,
  ListChecks,
  Package,
  Plug,
  Search,
  Settings,
  Settings2,
  ShoppingCart,
  Sparkles,
  Truck,
  Wallet,
  type LucideIcon,
} from "lucide-react";
import { NavLink } from "react-router-dom";

interface NavEntry {
  to: string;
  label: string;
  icon: LucideIcon;
  implemented: boolean;
}

interface NavGroup {
  title: string;
  entries: NavEntry[];
}

const GROUPS: NavGroup[] = [
  {
    title: "Overview",
    entries: [
      { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, implemented: true },
      { to: "/app-settings", label: "App Settings", icon: Settings2, implemented: true },
    ],
  },
  {
    title: "Connection & Setup",
    entries: [
      { to: "/connection", label: "Website Connection", icon: Plug, implemented: true },
      { to: "/site-setup", label: "Setup Wizard", icon: Settings, implemented: true },
      { to: "/wordpress-settings", label: "WordPress Settings", icon: Settings, implemented: true },
    ],
  },
  {
    title: "WooCommerce",
    entries: [
      { to: "/woocommerce", label: "Store Setup", icon: ShoppingCart, implemented: true },
      { to: "/cod", label: "Cash on Delivery", icon: Wallet, implemented: true },
      { to: "/shipping", label: "Shipping Zones", icon: Truck, implemented: true },
    ],
  },
  {
    title: "Publishing",
    entries: [
      { to: "/product-publisher", label: "Product Publisher", icon: Package, implemented: true },
      { to: "/blog-publisher", label: "Blog Publisher", icon: BookOpen, implemented: true },
      { to: "/page-publisher", label: "Page Publisher", icon: FileText, implemented: true },
      { to: "/queue", label: "Publishing Queue", icon: ListChecks, implemented: true },
    ],
  },
  {
    title: "Media",
    entries: [
      { to: "/media-studio", label: "Media Studio", icon: ImageIcon, implemented: true },
      { to: "/image-presets", label: "Image Presets", icon: Crop, implemented: true },
    ],
  },
  {
    title: "SEO",
    entries: [
      { to: "/rankmath", label: "Rank Math SEO", icon: Search, implemented: true },
      { to: "/internal-linking", label: "Internal Linking", icon: LinkIcon, implemented: true },
      { to: "/seo-audit", label: "Technical SEO Audit", icon: ClipboardCheck, implemented: true },
    ],
  },
  {
    title: "Content & Ops",
    entries: [
      { to: "/ai-prompt-studio", label: "AI Prompt Studio", icon: Sparkles, implemented: true },
      { to: "/history", label: "History and Logs", icon: History, implemented: true },
      { to: "/backup", label: "Backup and Restore", icon: DatabaseBackup, implemented: true },
    ],
  },
];

export function Sidebar(): JSX.Element {
  return (
    <aside className="flex h-full w-64 flex-col border-r border-surface-border bg-white">
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {GROUPS.map((group) => (
          <div key={group.title} className="mb-4">
            <p className="mb-1 px-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              {group.title}
            </p>
            <ul className="space-y-0.5">
              {group.entries.map((entry) => {
                const Icon = entry.icon;
                return (
                  <li key={entry.to}>
                    <NavLink
                      to={entry.to}
                      className={({ isActive }) =>
                        `flex items-center gap-2 rounded px-2 py-1.5 text-sm transition-colors ${
                          isActive
                            ? "bg-brand-light font-medium text-brand-dark"
                            : "text-slate-700 hover:bg-surface-muted"
                        }`
                      }
                    >
                      <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                      <span className="flex-1 truncate">{entry.label}</span>
                      {!entry.implemented ? (
                        <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                          soon
                        </span>
                      ) : null}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  );
}