/**
 * Route definitions.
 */

import { createBrowserRouter, Navigate } from "react-router-dom";

import { Layout } from "@/layout/Layout";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { AppSettingsPage } from "@/features/app-settings/AppSettingsPage";
import { ConnectionPage } from "@/features/connection/ConnectionPage";
import { MediaStudioPage } from "@/features/media-studio/MediaStudioPage";
import { BlogPublisherPage } from "@/features/blog-publisher/BlogPublisherPage";
import { PagePublisherPage } from "@/features/page-publisher/PagePublisherPage";
import { ProductPublisherPage } from "@/features/product-publisher/ProductPublisherPage";
import { WCSettingsPage } from "@/features/wordpress-settings/WCSettingsPage";
import { CODPage } from "@/features/cod/CODPage";
import { ShippingPage } from "@/features/shipping/ShippingPage";
import { SetupWizardPage } from "@/features/site-setup/SetupWizardPage";
import { ImagePresetsPage } from "@/features/image-presets/ImagePresetsPage";
import { RankMathPage } from "@/features/rankmath/RankMathPage";
import { InternalLinkingPage } from "@/features/internal-linking/InternalLinkingPage";
import { AIPromptStudioPage } from "@/features/ai-prompt-studio/AIPromptStudioPage";
import { SEOAuditPage } from "@/features/seo-audit/SEOAuditPage";
import { QueuePage } from "@/features/queue/QueuePage";
import { HistoryPage } from "@/features/history/HistoryPage";
import { BackupPage } from "@/features/backup/BackupPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "app-settings", element: <AppSettingsPage /> },
      { path: "connection", element: <ConnectionPage /> },
      { path: "media-studio", element: <MediaStudioPage /> },
      { path: "blog-publisher", element: <BlogPublisherPage /> },
      { path: "page-publisher", element: <PagePublisherPage /> },
      { path: "product-publisher", element: <ProductPublisherPage /> },
      { path: "wordpress-settings", element: <WCSettingsPage /> },
      { path: "woocommerce", element: <WCSettingsPage /> },
      { path: "cod", element: <CODPage /> },
      { path: "shipping", element: <ShippingPage /> },
      { path: "site-setup", element: <SetupWizardPage /> },
      { path: "image-presets", element: <ImagePresetsPage /> },
      { path: "rankmath", element: <RankMathPage /> },
      { path: "internal-linking", element: <InternalLinkingPage /> },
      { path: "ai-prompt-studio", element: <AIPromptStudioPage /> },
      { path: "seo-audit", element: <SEOAuditPage /> },
      { path: "queue", element: <QueuePage /> },
      { path: "history", element: <HistoryPage /> },
      { path: "backup", element: <BackupPage /> },
      { path: "*", element: <Navigate to="/dashboard" replace /> },
    ],
  },
]);