import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import HomePage from "./pages/HomePage";
import TripPlannerPage from "./pages/TripPlannerPage";

function getToken() {
  return localStorage.getItem("tb_token") || sessionStorage.getItem("tb_token");
}

function Protected({ children }) {
  return getToken() ? children : <Navigate to="/login" replace />;
}

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<Protected><HomePage /></Protected>} />
        <Route path="/plan" element={<Protected><TripPlannerPage /></Protected>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>
);
