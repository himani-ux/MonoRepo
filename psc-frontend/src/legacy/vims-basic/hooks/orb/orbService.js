// src/services/orbService.js
const API_BASE_URL = "http://localhost:8001/api/orb/api";

export const orbService = {
  // Fetch operations
  async fetchOperations(vesselId) {
    const response = await fetch(
      `${API_BASE_URL}/operations/?vessel_id=${vesselId}&is_deleted=false`
    );
    const data = await response.json();
    return Array.isArray(data) ? data : data.results || [];
  },

  // Fetch codes
  async fetchCodes() {
    const res = await fetch(`${API_BASE_URL}/codes/`);
    const data = await res.json();
    return Array.isArray(data) ? data : data.results || [];
  },

  // Fetch vessels
  async fetchVessels() {
    const res = await fetch(`${API_BASE_URL}/vessels/`);
    const data = await res.json();
    return Array.isArray(data) ? data : data.results || [];
  },

  // Fetch CSRF token
  async fetchCSRF() {
    const response = await fetch(`${API_BASE_URL}/csrf/`, {
      credentials: 'include'
    });
    const data = await response.json();
    return data.csrfToken;
  },

  // Approve entry
  async approveEntry(id, approvedBy) {
    const response = await fetch(`${API_BASE_URL}/operations/${id}/approve/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ approved_by: approvedBy }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(JSON.stringify(error));
    }

    return response.json();
  },

  // Reject entry
  async rejectEntry(id, rejectedBy) {
    const response = await fetch(`${API_BASE_URL}/operations/${id}/reject/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ rejected_by: rejectedBy }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(JSON.stringify(error));
    }

    return response.json();
  },

  // Create entry
  async createEntry(payload) {
    const response = await fetch(`${API_BASE_URL}/operations/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(JSON.stringify(err));
    }

    return response.json();
  },

  // Update print status
  async updatePrintStatus(updateData) {
    const response = await fetch(`${API_BASE_URL}/update-print-status/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updateData),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`${response.status} - ${errorText}`);
    }

    return response.json();
  },

  // Save PDF metadata
  async savePDFMetadata(metadataPayload) {
    const response = await fetch(`${API_BASE_URL}/save-pdf-metadata/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(metadataPayload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to save PDF metadata: ${response.status} - ${errorText}`);
    }

    return response.json();
  },

  // Get server internal IP
  async getInternalIP() {
    const response = await fetch(`${API_BASE_URL}/get-internal-ip/`);
    if (!response.ok) {
      throw new Error(`Failed to get server's local IP: ${response.status}`);
    }
    const data = await response.json();
    return data.internal_ip;
  },

  // Get last page number
  async getLastPageNumber(vesselId) {
    const response = await fetch(`http://localhost:8001/api/get_last_page_number/?vessel_id=${vesselId}`);
    const data = await response.json();
    return data.last_page || 0;
  }
};
