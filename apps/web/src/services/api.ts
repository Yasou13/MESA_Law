import axios from "axios";

// Base API instance (assuming it proxies to FastAPI backend)
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  }
});

export const qaAPI = {
  askQuestion: async (matterId: string, question: string) => {
    const response = await api.post(`/matters/${matterId}/qa`, { question });
    return response.data;
  }
};

export const draftAPI = {
  listDrafts: async (matterId: string) => {
    const response = await api.get(`/draft-studio/drafts/matter/${matterId}`);
    return response.data;
  },
  generateDraft: async (matterId: string, templateName: string = "default") => {
    const response = await api.post(`/draft-studio/drafts/generate`, { matter_id: matterId, template_name: templateName });
    return response.data;
  },
  getDraft: async (draftId: string) => {
    const response = await api.get(`/draft-studio/drafts/${draftId}`);
    return response.data;
  }
};

export const researchAPI = {
  startResearch: async (matterId: string, query: string) => {
    const response = await api.post(`/research/start`, { matter_id: matterId, query });
    return response.data;
  }
};

export const deadlineAPI = {
  listPotentialDeadlines: async (matterId: string) => {
    const response = await api.get(`/deadlines/potential/${matterId}`);
    return response.data;
  },
  approveDeadline: async (potentialDeadlineId: string, dueDate: string) => {
    const response = await api.post(`/deadlines/approve`, { potential_deadline_id: potentialDeadlineId, due_date: dueDate });
    return response.data;
  }
};
