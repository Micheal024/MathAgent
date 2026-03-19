/**
 * REST API Client for MathModelingAgent Backend.
 * Base URL is derived from page config and can be overridden at runtime.
 */

function resolveApiBase() {
    const override = window.__MATH_MODELING_CONFIG__?.apiBase;
    if (override) return override.replace(/\/$/, '');

    const meta = document.querySelector('meta[name="api-base"]')?.content?.trim();
    if (meta) return meta.replace(/\/$/, '');

    const host = window.location.hostname || 'localhost';
    return `http://${host}:8000/api/v1`;
}

const API_BASE = resolveApiBase();
const API_TIMEOUT = 5000; // 5 seconds

/** Fetch with timeout to prevent hanging. */
function fetchWithTimeout(url, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), API_TIMEOUT);
    return fetch(url, { ...options, signal: controller.signal })
        .finally(() => clearTimeout(timer));
}

const api = {
    /** List all projects. */
    async listProjects() {
        const res = await fetchWithTimeout(`${API_BASE}/projects`);
        if (!res.ok) throw new Error(`Failed to list projects: ${res.status}`);
        return res.json();
    },

    /** Create a new project. */
    async createProject(title, competition = 'MCM') {
        const res = await fetchWithTimeout(`${API_BASE}/projects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, competition }),
        });
        if (!res.ok) throw new Error(`Failed to create project: ${res.status}`);
        return res.json();
    },

    /** Get a project by ID. */
    async getProject(projectId) {
        const res = await fetchWithTimeout(`${API_BASE}/projects/${projectId}`);
        if (!res.ok) throw new Error(`Failed to get project: ${res.status}`);
        return res.json();
    },

    /** Get chat history for a project. */
    async getChatHistory(projectId) {
        const res = await fetchWithTimeout(`${API_BASE}/project/${projectId}/history`);
        if (!res.ok) throw new Error(`Failed to get chat history: ${res.status}`);
        return res.json();
    },

    /** Get artifacts for a project. */
    async getArtifacts(projectId) {
        const res = await fetchWithTimeout(`${API_BASE}/artifacts/${projectId}`);
        if (!res.ok) throw new Error(`Failed to get artifacts: ${res.status}`);
        return res.json();
    },

    /** Get workflow runtime state for a project. */
    async getWorkflowStatus(projectId) {
        const res = await fetchWithTimeout(`${API_BASE}/workflow/${projectId}`);
        if (!res.ok) throw new Error(`Failed to get workflow status: ${res.status}`);
        return res.json();
    },

    /** Upload a file for parsing. */
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetchWithTimeout(`${API_BASE}/upload/`, {
            method: 'POST',
            body: formData,
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            throw new Error(err.detail || `Upload failed: ${res.status}`);
        }
        return res.json();
    },

    /** Delete a project by ID. */
    async deleteProject(projectId) {
        const res = await fetchWithTimeout(`${API_BASE}/projects/${projectId}`, {
            method: 'DELETE',
        });
        if (!res.ok) throw new Error(`Failed to delete project: ${res.status}`);
    },
};
