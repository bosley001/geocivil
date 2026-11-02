export const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
const TOKEN_KEY = "geocivil-token";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export function saveToken(token: string | null) {
  if (token) sessionStorage.setItem(TOKEN_KEY, token);
  else sessionStorage.removeItem(TOKEN_KEY);
}

export function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError("Impossible de joindre le serveur. Vérifiez votre connexion et l’URL de l’API.", 0);
  }

  if (!response.ok) {
    let message = `Erreur ${response.status}`;
    try {
      const body = await response.json();
      message = typeof body.detail === "string" ? body.detail : message;
    } catch {
      // La réponse peut ne pas contenir de JSON.
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function download(path: string, filename: string) {
  const headers = new Headers();
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}${path}`, { headers });
  if (!response.ok) {
    let message = `Erreur ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      // La réponse peut ne pas contenir de JSON.
    }
    throw new ApiError(message, response.status);
  }
  const objectUrl = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(objectUrl);
}

export type User = { id: number; email: string; full_name: string; role: string };

export type ProjectInput = {
  name: string;
  city: string;
  building_type: "maison";
  soil: {
    soil_type: "laterite" | "argile" | "sable" | "gravier" | "roche" | "marais";
    bearing_capacity_kpa: number;
    water_table_depth_m: number;
    flood_zone: boolean;
    geotech_study: "none" | "sondages" | "rapport";
  };
  building: {
    footprint_m2: number;
    length_width_ratio: number;
    floors: number;
    floor_height_m: number;
    column_span_m: number;
    usage: "habitation" | "bureaux" | "commerce";
    roof_type: "tole" | "terrasse";
    roof_slope_pct: number;
  };
};

export type Project = ProjectInput & {
  id: number;
  norm: string;
  created_at: string;
  updated_at: string;
};

export type Analysis = {
  version_moteur?: string;
  toutes_verifications_ok?: boolean;
  verdict?: {
    niveau: string;
    texte: string;
    pression_moyenne_kPa: number;
    contrainte_admissible_kPa: number;
    taux: number;
  };
  geometrie?: { L_m: number; l_m: number; niveaux: number; poteaux_x: number; poteaux_y: number };
  fondations?: { type_retenu: string; classe_fissuration: string };
  alertes?: string[];
};

export type Quantities = {
  devis: { total_FCFA: number; cout_par_m2_FCFA: number; lignes: Record<string, Array<{ cle: string; designation: string; unite: string; quantite: number; pu: number; total: number }>> };
  metre: { ratios: { surface_batie_m2: number; beton_C25_m3: number; acier_kg_par_m3_beton: number }; avertissements: string[] };
  analyse_ok: boolean;
};