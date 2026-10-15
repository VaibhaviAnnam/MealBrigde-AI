// App.js – top-level routing
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import DonorDashboard from "./pages/DonorDashboard";
import NgoDashboard from "./pages/NgoDashboard";
import ImpactDashboard from "./pages/ImpactDashboard";

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/"       element={<Home />} />
        <Route path="/donor"  element={<DonorDashboard />} />
        <Route path="/ngo"    element={<NgoDashboard />} />
        <Route path="/impact" element={<ImpactDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
