import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { AppShell } from "@/components/AppShell";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Toaster } from "@/features/notifications/Toaster";
import AnalyticsPage from "@/pages/AnalyticsPage";
import CalendarPage from "@/pages/CalendarPage";
import CoachPage from "@/pages/CoachPage";
import CoursePage from "@/pages/CoursePage";
import DashboardPage from "@/pages/DashboardPage";
import FinancePage from "@/pages/FinancePage";
import JobTrackerPage from "@/pages/JobTrackerPage";
import LearningPage from "@/pages/LearningPage";
import LoginPage from "@/pages/LoginPage";
import ProjectBoardPage from "@/pages/ProjectBoardPage";
import ProjectsPage from "@/pages/ProjectsPage";
import RegisterPage from "@/pages/RegisterPage";
import SettingsPage from "@/pages/SettingsPage";

const protect = (el: React.ReactNode) => <ProtectedRoute>{el}</ProtectedRoute>;

export default function App() {
  const { pathname } = useLocation();
  const isAuthRoute = pathname === "/login" || pathname === "/register";

  if (isAuthRoute) {
    return (
      <>
        <Toaster />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </>
    );
  }

  return (
    <AppShell>
      <Toaster />
      <Routes>
        <Route path="/" element={protect(<DashboardPage />)} />
        <Route path="/job-tracker" element={protect(<JobTrackerPage />)} />
        <Route path="/projects" element={protect(<ProjectsPage />)} />
        <Route path="/projects/:projectId" element={protect(<ProjectBoardPage />)} />
        <Route path="/calendar" element={protect(<CalendarPage />)} />
        <Route path="/finance" element={protect(<FinancePage />)} />
        <Route path="/learning" element={protect(<LearningPage />)} />
        <Route path="/learning/courses/:courseId" element={protect(<CoursePage />)} />
        <Route path="/analytics" element={protect(<AnalyticsPage />)} />
        <Route path="/coach" element={protect(<CoachPage />)} />
        <Route path="/settings" element={protect(<SettingsPage />)} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
