// src/services/api.js
// Centralised Axios wrapper for all backend calls.

import axios from "axios";

const BASE = "http://localhost:5000/api";

const api = axios.create({ baseURL: BASE });

// ── Donations ──────────────────────────────────────────────────────────────

export const getDonations     = (params = {}) => api.get("/donations", { params });
export const getDonation      = (id)          => api.get(`/donations/${id}`);
export const createDonation   = (data)        => api.post("/donations", data);
export const updateDonation   = (id, data)    => api.patch(`/donations/${id}`, data);
export const deleteDonation   = (id)          => api.delete(`/donations/${id}`);

// ── NGOs ───────────────────────────────────────────────────────────────────

export const getNGOs          = ()            => api.get("/ngos");
export const getNGO           = (id)          => api.get(`/ngos/${id}`);
export const createNGO        = (data)        => api.post("/ngos", data);

// ── Claims ─────────────────────────────────────────────────────────────────

export const getClaims        = (params = {}) => api.get("/claims", { params });
export const createClaim      = (data)        => api.post("/claims", data);
export const updateClaimStatus = (id, status) =>
  api.patch(`/claims/${id}/status`, { status });

// ── Matching ───────────────────────────────────────────────────────────────

export const getMatches = (ngoId, params = {}) =>
  api.get(`/matches/${ngoId}`, { params });

// ── Impact ─────────────────────────────────────────────────────────────────

export const getImpact = () => api.get("/impact");
