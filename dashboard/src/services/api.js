import axios from "axios";
const BASE = "/api";
const api  = axios.create({ baseURL: BASE });

export const getFlagged    = ()           => api.get("/doctor/flagged");
export const getAllSessions = (limit=50)  => api.get(`/doctor/all?limit=${limit}`);
export const getSession    = (id)         => api.get(`/sessions/${id}`);
export const submitJudgment= (id, judgment, notes) =>
    api.post(`/doctor/${id}/judgment`, { judgment, notes });
