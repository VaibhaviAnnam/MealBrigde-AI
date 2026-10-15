// components/Navbar.jsx
import { NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-brand" style={{ textDecoration: "none" }}>
        MealBridge AI
      </NavLink>
      <ul className="navbar-links">
        <li>
          <NavLink to="/" className={({ isActive }) => isActive ? "active" : ""} end>
            Home
          </NavLink>
        </li>
        <li>
          <NavLink to="/donor" className={({ isActive }) => isActive ? "active" : ""}>
            Donor Dashboard
          </NavLink>
        </li>
        <li>
          <NavLink to="/ngo" className={({ isActive }) => isActive ? "active" : ""}>
            NGO Dashboard
          </NavLink>
        </li>
        <li>
          <NavLink to="/impact" className={({ isActive }) => isActive ? "active" : ""}>
            Impact
          </NavLink>
        </li>
      </ul>
    </nav>
  );
}
