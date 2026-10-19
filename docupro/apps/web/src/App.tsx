import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { ToastProvider } from "@/components/Toast";
import { HomePage } from "@/pages/Home";
import { ToolsPage } from "@/pages/Tools";
import { ToolDetailPage } from "@/pages/ToolDetail";
import { RecentPage } from "@/pages/Recent";
import { SettingsPage } from "@/pages/Settings";
import { PrivacyPage } from "@/pages/Privacy";
import { AboutPage } from "@/pages/About";
import { NotFoundPage } from "@/pages/NotFound";

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="tools" element={<ToolsPage />} />
            <Route path="tool/:toolId" element={<ToolDetailPage />} />
            <Route path="recent" element={<RecentPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="privacy" element={<PrivacyPage />} />
            <Route path="about" element={<AboutPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </ToastProvider>
    </BrowserRouter>
  );
}
