import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import HomePage from "./pages/HomePage";
import TripPlannerPage from "./pages/TripPlannerPage";
import MyTripsPage from "./pages/MyTripsPage";
import FlightsPage from "./pages/FlightsPage";
import HotelsPage from "./pages/HotelsPage";
import CommunityPage from "./pages/CommunityPage";

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
        <Route path="/my-trips" element={<Protected><MyTripsPage /></Protected>} />
        <Route path="/flights" element={<Protected><FlightsPage /></Protected>} />
        <Route path="/hotels" element={<Protected><HotelsPage /></Protected>} />
        <Route path="/community" element={<Protected><CommunityPage /></Protected>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>
);
