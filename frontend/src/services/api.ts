import type { KtruGroup, KtruPosition, PostscriptTemplate, SelectedCharacteristic, TechnicalSpec, User } from "../types/domain";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

type LoginResult = { token: string; user: User };

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

class ApiClient {
  token = localStorage.getItem("token") || "";

  setToken(token: string) {
    this.token = token;
    localStorage.setItem("token", token);
  }

  clearToken() {
    this.token = "";
    localStorage.removeItem("token");
  }

  private parseResponseText(text: string, contentType: string | null) {
    if (!text) return null;
    if (contentType?.includes("application/json")) {
      return JSON.parse(text);
    }
    return text;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(this.token ? { Authorization: `Token ${this.token}` } : {}),
        ...(options.headers || {}),
      },
    });
    const text = await response.text();
    let data: any = null;
    try {
      data = this.parseResponseText(text, response.headers.get("content-type"));
    } catch {
      data = text || null;
    }
    if (!response.ok) {
      const detail =
        data?.detail ||
        data?.non_field_errors?.join?.(", ") ||
        (typeof data === "string" ? data.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim() : JSON.stringify(data));
      throw new ApiError(detail || "Ошибка запроса", response.status, data);
    }
    return data as T;
  }

  register(email: string, password: string) {
    return this.request<{ user: User; status: string }>("/auth/register/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async login(email: string, password: string) {
    const result = await this.request<LoginResult>("/auth/login/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.setToken(result.token);
    return result;
  }

  me() {
    return this.request<User>("/auth/me/");
  }

  specs(search = "") {
    const query = search ? `?search=${encodeURIComponent(search)}` : "";
    return this.request<TechnicalSpec[]>(`/specs/${query}`);
  }

  createSpec(title: string) {
    return this.request<TechnicalSpec>("/specs/", {
      method: "POST",
      body: JSON.stringify({ title, status: "draft" }),
    });
  }

  updateSpec(id: number, payload: Partial<TechnicalSpec>) {
    return this.request<TechnicalSpec>(`/specs/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  deleteSpec(id: number) {
    return this.request<void>(`/specs/${id}/`, { method: "DELETE" });
  }

  copySpec(id: number) {
    return this.request<TechnicalSpec>(`/specs/${id}/copy/`, { method: "POST" });
  }

  previewSpec(id: number) {
    return this.request<TechnicalSpec>(`/specs/${id}/preview/`);
  }

  postscriptTemplates() {
    return this.request<PostscriptTemplate[]>("/postscript-templates/");
  }

  groups() {
    return this.request<KtruGroup[]>("/ktru/groups/");
  }

  searchPositions(q: string) {
    return this.request<KtruPosition[]>(`/ktru/positions/?q=${encodeURIComponent(q)}`);
  }

  positionsByGroup(groupId: number) {
    return this.request<KtruPosition[]>(`/ktru/positions/?group_id=${groupId}`);
  }

  position(id: number) {
    return this.request<KtruPosition>(`/ktru/positions/${id}/`);
  }

  resolveRefined(group_id: number, value: string) {
    return this.request<KtruPosition>("/ktru/resolve-refined/", {
      method: "POST",
      body: JSON.stringify({ group_id, value }),
    });
  }

  addItem(
    specId: number,
    payload: {
      position_number: number;
      ktru_position: number;
      object_name: string;
      quantity: string;
      unit_name: string;
      display_order: number;
      characteristics: SelectedCharacteristic[];
    },
  ) {
    return this.request(`/specs/${specId}/items/`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  updateItem(
    specId: number,
    itemId: number,
    payload: {
      position_number: number;
      ktru_position: number;
      object_name: string;
      quantity: string;
      unit_name: string;
      display_order: number;
      characteristics: SelectedCharacteristic[];
    },
  ) {
    return this.request(`/specs/${specId}/items/${itemId}/`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  deleteItem(specId: number, itemId: number) {
    return this.request<void>(`/specs/${specId}/items/${itemId}/`, { method: "DELETE" });
  }

  exportSpec(specId: number, format: "docx" | "xlsx" | "pdf") {
    return this.request<{ url: string; format: string; export_id: number }>(`/specs/${specId}/export/${format}/`);
  }
}

export const api = new ApiClient();
