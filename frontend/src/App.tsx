import { FormEvent, useEffect, useState } from "react";
import {
  Activity,
  ArrowLeft,
  ArrowRight,
  Building2,
  Check,
  ClipboardList,
  FileSpreadsheet,
  FileText,
  Layers,
  LogOut,
  MapPin,
  Pencil,
  Plus,
  Ruler,
  Search,
  Share2,
  ShieldCheck,
  Trash2,
  X,
  Zap,
} from "lucide-react";
import { BrowserRouter, Link, Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";
import { Analysis, api, download, getToken, Project, ProjectInput, Quantities, saveToken, User } from "./api";

const initialProject: ProjectInput = {
  name: "",
  city: "Douala",
  building_type: "maison",
  soil: {
    soil_type: "laterite",
    bearing_capacity_kpa: 200,
    water_table_depth_m: 3,
    flood_zone: false,
    geotech_study: "none",
  },
  building: {
    footprint_m2: 120,
    length_width_ratio: 1.5,
    floors: 1,
    floor_height_m: 3,
    column_span_m: 4,
    usage: "habitation",
    roof_type: "tole",
    roof_slope_pct: 30,
  },
};

function formatMoney(value?: number) {
  return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 }).format(value ?? 0);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("fr-FR", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
}

function errorText(error: unknown) {
  return error instanceof Error ? error.message : "Une erreur inattendue est survenue.";
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/shared/:token" element={<SharedPage />} />
        <Route path="*" element={<AuthGate />} />
      </Routes>
    </BrowserRouter>
  );
}

function AuthGate() {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setChecking(false);
      return;
    }
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => saveToken(null))
      .finally(() => setChecking(false));
  }, []);

  async function authenticate(token: string) {
    saveToken(token);
    try {
      setUser(await api<User>("/auth/me"));
    } catch (error) {
      saveToken(null);
      throw error;
    }
  }

  if (checking) return <div className="boot-screen"><span className="loader" />GéoCivil</div>;
  if (!user) return <AuthPage onAuthenticated={authenticate} />;
  return <AppShell user={user} onLogout={() => { saveToken(null); setUser(null); }} />;
}

function AuthPage({ onAuthenticated }: { onAuthenticated: (token: string) => Promise<void> }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const body = mode === "register" ? { email, password, full_name: name } : { email, password };
      const result = await api<{ access_token: string }>(`/auth/${mode === "register" ? "register" : "login"}`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      await onAuthenticated(result.access_token);
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-story">
        <div className="auth-photo" />
        <Link className="brand brand-light" to="/">
          <span className="brand-mark"><Building2 size={20} strokeWidth={2.2} /></span>
          <span>GéoCivil<span className="brand-period">.</span></span>
        </Link>
        <div className="story-copy">
          <span className="eyebrow eyebrow-light">ÉTUDES · CONSTRUCTION · CAMEROUN</span>
          <h1>Des fondations<br />solides, dès la<br /><em>première esquisse.</em></h1>
          <p>Dimensionnez, vérifiez et pilotez vos projets de construction dans un espace unique.</p>
        </div>
        <div className="story-foot"><span>BAEL 91 modifié 99</span><span>Pré-dimensionnement structurel</span></div>
      </section>
      <section className="auth-panel">
        <div className="auth-mobile-brand"><span className="brand-mark"><Building2 size={19} /></span>GéoCivil<span className="brand-period">.</span></div>
        <div className="auth-form-wrap">
          <span className="eyebrow">VOTRE ESPACE DE TRAVAIL</span>
          <h2>{mode === "login" ? "Bon retour." : "Créer votre compte."}</h2>
          <p className="muted auth-intro">{mode === "login" ? "Connectez-vous pour retrouver vos études et vos projets." : "Quelques informations pour démarrer votre espace GéoCivil."}</p>
          <form onSubmit={submit} className="form-stack">
            {mode === "register" && <label className="field"><span>Nom complet</span><input autoComplete="name" value={name} onChange={(event) => setName(event.target.value)} placeholder="Ex. Amina Nguema" maxLength={120} /></label>}
            <label className="field"><span>Adresse e-mail</span><input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="vous@entreprise.com" /></label>
            <label className="field"><span>Mot de passe</span><input type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} required minLength={mode === "register" ? 8 : undefined} maxLength={72} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="8 caractères minimum" /></label>
            {error && <div className="form-error" role="alert">{error}</div>}
            <button className="button button-primary button-wide" disabled={busy} type="submit">{busy ? <span className="loader loader-light" /> : mode === "login" ? "Se connecter" : "Créer mon compte"}<ArrowRight size={17} /></button>
          </form>
          <p className="auth-switch">{mode === "login" ? "Pas encore de compte ?" : "Vous avez déjà un compte ?"}{" "}<button className="text-button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>{mode === "login" ? "Créer un compte" : "Se connecter"}</button></p>
          <div className="security-note"><ShieldCheck size={16} /><span>Vos études restent privées et accessibles uniquement avec votre compte.</span></div>
        </div>
        <span className="auth-copyright">GéoCivil · Outil d’aide à la décision technique</span>
      </section>
    </main>
  );
}

function AppShell({ user, onLogout }: { user: User; onLogout: () => void }) {
  const location = useLocation();
  const title = location.pathname.startsWith("/prices") ? "Prix & matériaux" : location.pathname.includes("/projects/") ? "Étude de projet" : "Espace projets";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link to="/" className="brand brand-sidebar"><span className="brand-mark"><Building2 size={20} /></span><span>GéoCivil<span className="brand-period">.</span></span></Link>
        <div className="side-caption">ESPACE DE TRAVAIL</div>
        <nav className="side-nav">
          <Link to="/" className={`side-link ${location.pathname === "/" ? "active" : ""}`}><Layers size={18} /><span>Mes projets</span><ArrowRight className="nav-arrow" size={15} /></Link>
          <Link to="/prices" className={`side-link ${location.pathname.startsWith("/prices") ? "active" : ""}`}><ClipboardList size={18} /><span>Prix & matériaux</span><ArrowRight className="nav-arrow" size={15} /></Link>
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-plan"><span className="plan-icon"><Activity size={17} /></span><div><strong>Calcul BAEL</strong><small>Norme 91 mod. 99</small></div><span className="live-dot" /></div>
          <div className="user-profile"><div className="avatar">{(user.full_name || user.email).slice(0, 1).toUpperCase()}</div><div className="user-meta"><strong>{user.full_name || "Mon compte"}</strong><small>{user.email}</small></div><button className="icon-button logout-button" title="Se déconnecter" onClick={onLogout}><LogOut size={17} /></button></div>
        </div>
      </aside>
      <main className="main-area">
        <header className="topbar"><div className="breadcrumbs"><span>GéoCivil</span><span className="crumb-slash">/</span><strong>{title}</strong></div><div className="topbar-right"><span className="topbar-standard"><span className="status-dot" />BAEL 91 · 99</span><div className="topbar-avatar">{(user.full_name || user.email).slice(0, 1).toUpperCase()}</div></div></header>
        <div className="page-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects/new" element={<ProjectEditor />} />
            <Route path="/projects/:id/edit" element={<ProjectEditor />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
            <Route path="/prices" element={<PricesPage user={user} />} />
            <Route path="*" element={<Dashboard />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Project[]>("/projects").then(setProjects).catch((caught) => setError(errorText(caught))).finally(() => setLoading(false));
  }, []);

  const area = projects.reduce((total, project) => total + project.building.footprint_m2 * (project.building.floors + 1), 0);
  return (
    <>
      <section className="page-heading dashboard-heading">
        <div><span className="eyebrow">VOTRE ACTIVITÉ</span><h1>Un projet bien pensé<br /><em>commence ici.</em></h1><p className="muted">Retrouvez vos études de structure et avancez avec des bases claires.</p></div>
        <Link to="/projects/new" className="button button-primary"><Plus size={18} />Nouveau projet</Link>
      </section>
      <section className="metric-row" aria-label="Indicateurs des projets">
        <Metric label="Projets suivis" value={loading ? "—" : String(projects.length).padStart(2, "0")} icon={<Building2 size={18} />} note="dans votre espace" />
        <Metric label="Surface étudiée" value={loading ? "—" : `${formatMoney(area)} m²`} icon={<Ruler size={18} />} note="surface cumulée" />
        <Metric label="Référentiel" value="BAEL 91" icon={<ShieldCheck size={18} />} note="modifié 99" />
      </section>
      <section className="section-block">
        <div className="section-title-row"><div><span className="eyebrow">BIBLIOTHÈQUE</span><h2>Projets récents</h2></div><span className="count-label">{projects.length} projet{projects.length > 1 ? "s" : ""}</span></div>
        {error && <div className="form-error" role="alert">{error}</div>}
        {loading ? <div className="loading-row"><span className="loader" />Chargement de vos projets...</div> : projects.length ? (
          <div className="project-list">
            {projects.map((project, index) => <Link className="project-row" to={`/projects/${project.id}`} key={project.id}>
              <span className={`project-index index-${index % 4}`}>{String(index + 1).padStart(2, "0")}</span>
              <span className="project-main"><strong>{project.name}</strong><small><MapPin size={13} />{project.city}</small></span>
              <span className="project-spec"><Building2 size={15} />{project.building.floors + 1} niveau{project.building.floors ? "x" : ""}</span>
              <span className="project-spec"><Ruler size={15} />{formatMoney(project.building.footprint_m2)} m²</span>
              <span className="project-date">Mis à jour le {formatDate(project.updated_at)}</span>
              <span className="project-open"><ArrowRight size={18} /></span>
            </Link>)}
          </div>
        ) : <div className="empty-state"><span className="empty-icon"><Building2 size={24} /></span><div><h3>Votre premier projet commence ici</h3><p>Renseignez le sol et le bâtiment pour obtenir une première étude de structure.</p></div><Link to="/projects/new" className="button button-outline"><Plus size={17} />Créer un projet</Link></div>}
      </section>
      <div className="dashboard-note"><span className="note-mark"><Zap size={17} /></span><div><strong>Une base technique, pas un plan d’exécution</strong><p>Les résultats sont un pré-dimensionnement à valider par un ingénieur agréé avant tout chantier.</p></div><span className="note-standard">BAEL · CAMEROUN</span></div>
    </>
  );
}

function Metric({ label, value, icon, note }: { label: string; value: string; icon: React.ReactNode; note: string }) {
  return <div className="metric"><span className="metric-icon">{icon}</span><span className="metric-label">{label}</span><strong>{value}</strong><small>{note}</small></div>;
}

function ProjectEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState<ProjectInput>(() => structuredClone(initialProject));
  const [loading, setLoading] = useState(Boolean(id));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    api<Project>(`/projects/${id}`).then(({ id: _id, norm: _norm, created_at: _created, updated_at: _updated, ...project }) => setForm(project)).catch((caught) => setError(errorText(caught))).finally(() => setLoading(false));
  }, [id]);

  function setSoil<K extends keyof ProjectInput["soil"]>(key: K, value: ProjectInput["soil"][K]) {
    setForm((current) => ({ ...current, soil: { ...current.soil, [key]: value } }));
  }
  function setBuilding<K extends keyof ProjectInput["building"]>(key: K, value: ProjectInput["building"][K]) {
    setForm((current) => ({ ...current, building: { ...current.building, [key]: value } }));
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const saved = await api<Project>(id ? `/projects/${id}` : "/projects", { method: id ? "PUT" : "POST", body: JSON.stringify(form) });
      navigate(`/projects/${saved.id}`);
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <div className="loading-row"><span className="loader" />Chargement du projet...</div>;
  return (
    <>
      <Link to={id ? `/projects/${id}` : "/"} className="back-link"><ArrowLeft size={16} />Retour aux projets</Link>
      <section className="page-heading compact-heading"><div><span className="eyebrow">{id ? "MISE À JOUR" : "NOUVELLE ÉTUDE"}</span><h1>{id ? "Modifier le projet" : "Définir votre projet."}</h1><p className="muted">Les hypothèses saisies alimentent le pré-dimensionnement BAEL.</p></div></section>
      <form className="editor-form" onSubmit={submit}>
        <section className="form-section"><div className="form-section-head"><span className="section-number">01</span><div><h2>Identification</h2><p>Les informations générales de l’ouvrage.</p></div></div>
          <div className="form-grid"><Field label="Nom du projet"><input required minLength={1} maxLength={160} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Ex. Villa Bonapriso" /></Field><Field label="Ville"><input required minLength={1} maxLength={120} value={form.city} onChange={(event) => setForm({ ...form, city: event.target.value })} placeholder="Ex. Douala" /></Field><Field label="Type d’ouvrage"><select value="maison" disabled><option value="maison">Maison individuelle</option></select></Field></div>
        </section>
        <section className="form-section"><div className="form-section-head"><span className="section-number">02</span><div><h2>Sol & fondations</h2><p>Valeurs de l’étude géotechnique ou estimations disponibles.</p></div></div>
          <div className="form-grid"><Field label="Nature du sol"><select value={form.soil.soil_type} onChange={(event) => setSoil("soil_type", event.target.value as ProjectInput["soil"]["soil_type"])}><option value="laterite">Latérite</option><option value="argile">Argile</option><option value="sable">Sable</option><option value="gravier">Gravier</option><option value="roche">Roche</option><option value="marais">Marécageux</option></select></Field><NumberField label="Contrainte admissible" suffix="kPa" value={form.soil.bearing_capacity_kpa} min={20} max={1500} onChange={(value) => setSoil("bearing_capacity_kpa", value)} /><NumberField label="Profondeur de la nappe" suffix="m" value={form.soil.water_table_depth_m} min={0} max={50} step={0.1} onChange={(value) => setSoil("water_table_depth_m", value)} /><Field label="Étude géotechnique"><select value={form.soil.geotech_study} onChange={(event) => setSoil("geotech_study", event.target.value as ProjectInput["soil"]["geotech_study"])}><option value="none">Aucune étude</option><option value="sondages">Sondages réalisés</option><option value="rapport">Rapport disponible</option></select></Field></div>
          <label className="check-field"><input type="checkbox" checked={form.soil.flood_zone} onChange={(event) => setSoil("flood_zone", event.target.checked)} /><span className="check-custom"><Check size={13} /></span><span>Le terrain se situe en zone inondable</span></label>
        </section>
        <section className="form-section"><div className="form-section-head"><span className="section-number">03</span><div><h2>Géométrie du bâtiment</h2><p>Gabarit principal et usage des niveaux.</p></div></div>
          <div className="form-grid"><NumberField label="Emprise au sol" suffix="m²" value={form.building.footprint_m2} min={10} max={2000} onChange={(value) => setBuilding("footprint_m2", value)} /><NumberField label="Nombre d’étages au-dessus du RDC" suffix="étage(s)" value={form.building.floors} min={0} max={2} step={1} onChange={(value) => setBuilding("floors", value)} /><NumberField label="Rapport longueur / largeur" value={form.building.length_width_ratio} min={1} max={3} step={0.1} onChange={(value) => setBuilding("length_width_ratio", value)} /><NumberField label="Portée entre poteaux" suffix="m" value={form.building.column_span_m} min={2.5} max={6} step={0.1} onChange={(value) => setBuilding("column_span_m", value)} /><NumberField label="Hauteur d’un niveau" suffix="m" value={form.building.floor_height_m} min={2.4} max={4} step={0.1} onChange={(value) => setBuilding("floor_height_m", value)} /><Field label="Usage principal"><select value={form.building.usage} onChange={(event) => setBuilding("usage", event.target.value as ProjectInput["building"]["usage"])}><option value="habitation">Habitation</option><option value="bureaux">Bureaux</option><option value="commerce">Commerce</option></select></Field><Field label="Type de toiture"><select value={form.building.roof_type} onChange={(event) => setBuilding("roof_type", event.target.value as ProjectInput["building"]["roof_type"])}><option value="tole">Tôle et charpente</option><option value="terrasse">Toiture terrasse</option></select></Field>{form.building.roof_type === "tole" && <NumberField label="Pente de toiture" suffix="%" value={form.building.roof_slope_pct} min={0} max={100} onChange={(value) => setBuilding("roof_slope_pct", value)} />}</div>
        </section>
        {error && <div className="form-error" role="alert">{error}</div>}
        <div className="form-footer"><p><ShieldCheck size={16} />Calcul indicatif à valider par un ingénieur agréé.</p><button className="button button-primary" disabled={busy}>{busy ? <span className="loader loader-light" /> : <>{id ? "Enregistrer les modifications" : "Créer le projet"}<ArrowRight size={17} /></>}</button></div>
      </form>
    </>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="field"><span>{label}</span>{children}</label>;
}

function NumberField({ label, suffix, value, min, max, step = 1, onChange }: { label: string; suffix?: string; value: number; min: number; max: number; step?: number; onChange: (value: number) => void }) {
  return <Field label={label}><span className="input-suffix-wrap"><input type="number" required value={value} min={min} max={max} step={step} onChange={(event) => onChange(Number(event.target.value))} />{suffix && <small>{suffix}</small>}</span></Field>;
}

function ProjectDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [quantities, setQuantities] = useState<Quantities | null>(null);
  const [shares, setShares] = useState<Array<{ id: number; label: string; active: boolean; expires_at: string | null }>>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [newShareUrl, setNewShareUrl] = useState("");

  async function refresh() {
    const item = await api<Project>(`/projects/${id}`);
    setProject(item);
    const [analysisResult, quantitiesResult, sharesResult] = await Promise.allSettled([
      api<Analysis>(`/projects/${id}/analysis`),
      api<Quantities>(`/projects/${id}/quantities`),
      api<Array<{ id: number; label: string; active: boolean; expires_at: string | null }>>(`/projects/${id}/shares`),
    ]);
    setAnalysis(analysisResult.status === "fulfilled" ? analysisResult.value : null);
    setQuantities(quantitiesResult.status === "fulfilled" ? quantitiesResult.value : null);
    setShares(sharesResult.status === "fulfilled" ? sharesResult.value : []);
  }

  useEffect(() => {
    refresh().catch((caught) => setError(errorText(caught))).finally(() => setLoading(false));
  }, [id]);

  async function runAnalysis() {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await api<Analysis>(`/projects/${id}/analysis`, { method: "POST" });
      setAnalysis(result);
      setQuantities(await api<Quantities>(`/projects/${id}/quantities`));
      setNotice("Analyse terminée et enregistrée.");
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setBusy(false);
    }
  }

  async function createShare() {
    setBusy(true);
    setError("");
    try {
      const share = await api<{ token: string }>(`/projects/${id}/shares`, { method: "POST", body: JSON.stringify({ label: "Partage client", include_prices: false, expires_in_days: 30 }) });
      const url = `${window.location.origin}/shared/${share.token}`;
      setNewShareUrl(url);
      try {
        await navigator.clipboard.writeText(url);
        setNotice("Lien de partage copié. Il expirera dans 30 jours.");
      } catch {
        setNotice("Lien créé. Copiez-le depuis le champ ci-dessous ; il expirera dans 30 jours.");
      }
      setShares(await api(`/projects/${id}/shares`));
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setBusy(false);
    }
  }

  async function revokeShare(shareId: number) {
    try {
      await api(`/projects/${id}/shares/${shareId}`, { method: "DELETE" });
      setShares(await api(`/projects/${id}/shares`));
      setNotice("Lien de partage révoqué.");
    } catch (caught) {
      setError(errorText(caught));
    }
  }

  async function removeProject() {
    if (!window.confirm("Supprimer ce projet et ses analyses ? Cette action est définitive.")) return;
    try {
      await api(`/projects/${id}`, { method: "DELETE" });
      navigate("/");
    } catch (caught) {
      setError(errorText(caught));
    }
  }

  async function saveFile(path: string, filename: string) {
    setError("");
    try {
      await download(path, filename);
    } catch (caught) {
      setError(errorText(caught));
    }
  }

  if (loading) return <div className="loading-row"><span className="loader" />Chargement de l’étude...</div>;
  if (!project) return <div className="empty-state"><div><h3>Projet indisponible</h3><p>{error || "Ce projet n’existe pas ou vous n’y avez pas accès."}</p></div><Link className="button button-outline" to="/">Retour aux projets</Link></div>;
  const level = analysis?.verdict?.niveau;
  const statusClass = level === "bad" ? "status-bad" : level === "warn" ? "status-warn" : "status-good";

  return (
    <>
      <Link to="/" className="back-link"><ArrowLeft size={16} />Tous les projets</Link>
      <section className="detail-heading"><div><span className="eyebrow">ÉTUDE · {project.norm}</span><h1>{project.name}</h1><div className="detail-location"><MapPin size={15} />{project.city}<span className="location-sep">·</span>Mis à jour le {formatDate(project.updated_at)}</div></div><div className="detail-actions"><Link className="button button-outline" to={`/projects/${id}/edit`}><Pencil size={16} />Modifier</Link><button className="icon-button danger-icon" title="Supprimer le projet" onClick={removeProject}><Trash2 size={17} /></button></div></section>
      {error && <div className="form-error" role="alert">{error}</div>}{notice && <div className="form-success" role="status"><Check size={16} />{notice}<button className="icon-button" onClick={() => setNotice("")} aria-label="Fermer"><X size={15} /></button></div>}
      <section className="project-summary">
        <div><span>EMPRISE</span><strong>{formatMoney(project.building.footprint_m2)} <small>m²</small></strong></div><div><span>NIVEAUX</span><strong>R+{project.building.floors}</strong></div><div><span>SOL</span><strong className="summary-word">{project.soil.soil_type}</strong></div><div><span>PORTÉE</span><strong>{project.building.column_span_m} <small>m</small></strong></div>
      </section>
      <section className="analysis-section">
        <div className="section-title-row"><div><span className="eyebrow">CALCUL STRUCTUREL</span><h2>Analyse BAEL</h2></div><button className="button button-primary" disabled={busy} onClick={runAnalysis}>{busy ? <span className="loader loader-light" /> : <><Zap size={16} />{analysis ? "Relancer l’analyse" : "Lancer l’analyse"}</>}</button></div>
        {analysis ? <div className="analysis-content">
          <div className={`verdict-panel ${statusClass}`}><span className="verdict-icon">{level === "bad" ? <X size={20} /> : <Check size={20} />}</span><div><span className="eyebrow">AVIS DE PRÉ-DIMENSIONNEMENT</span><h3>{analysis.verdict?.texte || "Analyse calculée"}</h3><p>Version moteur {analysis.version_moteur || "—"} · {analysis.toutes_verifications_ok ? "Vérifications satisfaites" : "Vérifications à examiner"}</p></div><strong className="verdict-rate">{formatMoney(analysis.verdict?.taux ? Math.round(analysis.verdict.taux * 100) : 0)}<small>% sol</small></strong></div>
          <div className="analysis-metrics"><div><span>Pression moyenne</span><strong>{analysis.verdict?.pression_moyenne_kPa ?? "—"}<small> kPa</small></strong></div><div><span>Contrainte admissible</span><strong>{analysis.verdict?.contrainte_admissible_kPa ?? "—"}<small> kPa</small></strong></div><div><span>Fondations retenues</span><strong className="metric-text">{analysis.fondations?.type_retenu || "—"}</strong></div><div><span>Trame calculée</span><strong>{analysis.geometrie ? `${analysis.geometrie.poteaux_x} × ${analysis.geometrie.poteaux_y}` : "—"}<small> poteaux</small></strong></div></div>
          {!!analysis.alertes?.length && <div className="alert-list">{analysis.alertes.map((alert) => <p key={alert}><span>!</span>{alert}</p>)}</div>}
        </div> : <div className="analysis-empty"><div className="analysis-empty-icon"><Activity size={23} /></div><div><h3>Aucune analyse enregistrée</h3><p>Lancez le calcul pour obtenir les vérifications, les sections et les recommandations de fondations.</p></div></div>}
      </section>
      {quantities && <section className="estimate-section"><div className="section-title-row"><div><span className="eyebrow">MÉTRÉ & ESTIMATION</span><h2>Enveloppe indicative</h2></div><div className="export-actions"><button className="button button-outline" onClick={() => saveFile(`/projects/${id}/report.pdf?prices=true`, `note-de-calcul-${id}.pdf`)}><FileText size={16} />Rapport PDF</button><button className="button button-outline" onClick={() => saveFile(`/projects/${id}/export/devis.xlsx`, `devis-${id}.xlsx`)}><FileSpreadsheet size={16} />Devis Excel</button></div></div><div className="estimate-band"><div><span>ESTIMATION TOTALE</span><strong>{formatMoney(quantities.devis.total_FCFA)} <small>FCFA</small></strong></div><div><span>COÛT PAR M² BÂTI</span><strong>{formatMoney(quantities.devis.cout_par_m2_FCFA)} <small>FCFA / m²</small></strong></div><div><span>BÉTON C25</span><strong>{quantities.metre.ratios.beton_C25_m3} <small>m³</small></strong></div><div><span>ACIER MOYEN</span><strong>{quantities.metre.ratios.acier_kg_par_m3_beton} <small>kg / m³</small></strong></div></div>{quantities.metre.avertissements.map((warning) => <p className="estimate-warning" key={warning}>{warning}</p>)}</section>}
      <section className="share-section"><div className="section-title-row"><div><span className="eyebrow">COLLABORATION</span><h2>Liens de partage</h2></div><button className="button button-outline" disabled={busy} onClick={createShare}><Share2 size={16} />Créer un lien en lecture seule</button></div>{newShareUrl && <div className="share-created"><input aria-label="Lien de partage nouvellement créé" readOnly value={newShareUrl} onFocus={(event) => event.target.select()} /><button className="text-button" onClick={async () => { try { await navigator.clipboard.writeText(newShareUrl); setNotice("Lien copié."); } catch { setNotice("Sélectionnez le lien pour le copier."); } }}>Copier</button></div>}{shares.length > 0 ? <div className="share-list">{shares.map((share) => <div className="share-row" key={share.id}><span className={`share-state ${share.active ? "is-active" : ""}`} /><span className="share-label">{share.label || "Lien de partage"}</span><span className="share-expiry">{share.expires_at ? `Expire le ${formatDate(share.expires_at)}` : "Sans expiration"}</span>{share.active && <button className="text-button revoke-button" onClick={() => revokeShare(share.id)}>Révoquer</button>}</div>)}</div> : <p className="muted share-empty">Aucun lien actif pour ce projet.</p>}</section>
      <div className="technical-disclaimer"><ShieldCheck size={17} /><p>Cette étude constitue un pré-dimensionnement indicatif. Elle ne remplace ni une étude géotechnique ni les plans d’exécution validés par un ingénieur agréé.</p></div>
    </>
  );
}

type Price = { key: string; label: string; unit: string; value: number; source: "default" | "city" | "user" };

function PricesPage({ user }: { user: User }) {
  const [city, setCity] = useState("Douala");
  const [query, setQuery] = useState("");
  const [prices, setPrices] = useState<Price[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadPrices(selectedCity: string) {
    setLoading(true);
    setError("");
    try {
      const result = await api<Price[]>(`/prices?city=${encodeURIComponent(selectedCity)}`);
      setPrices(result);
      setValues(Object.fromEntries(result.map((price) => [price.key, String(price.value)])));
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadPrices(city); }, []);

  async function savePrice(price: Price) {
    setError("");
    setNotice("");
    const value = Number(values[price.key]);
    if (!Number.isFinite(value) || value < 0) {
      setError("Saisissez un prix positif ou nul.");
      return;
    }
    try {
      if (user.role === "admin") {
        await api("/admin/prices", { method: "PUT", body: JSON.stringify({ key: price.key, city, value }) });
      } else {
        await api("/prices/overrides", { method: "PUT", body: JSON.stringify({ key: price.key, value }) });
      }
      setNotice(user.role === "admin" ? `Prix de ${city} mis à jour.` : "Votre ajustement a été enregistré.");
      await loadPrices(city);
    } catch (caught) {
      setError(errorText(caught));
    }
  }

  const filtered = prices.filter((price) => `${price.label} ${price.key}`.toLowerCase().includes(query.toLowerCase()));
  return (
    <>
      <section className="page-heading price-heading"><div><span className="eyebrow">BIBLIOTHÈQUE DE PRIX</span><h1>Des estimations<br /><em>ancrées au terrain.</em></h1><p className="muted">Consultez les prix indicatifs et ajustez-les à votre marché local.</p></div><span className="price-location"><MapPin size={17} />{city}</span></section>
      <section className="price-toolbar"><form className="city-form" onSubmit={(event) => { event.preventDefault(); loadPrices(city); }}><label className="field"><span>Ville du projet</span><input value={city} maxLength={120} onChange={(event) => setCity(event.target.value)} /></label><button className="button button-primary">Actualiser</button></form><label className="search-field"><span className="sr-only">Rechercher un matériau</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Rechercher un poste" /><Search size={16} /></label></section>
      {error && <div className="form-error" role="alert">{error}</div>}{notice && <div className="form-success" role="status"><Check size={16} />{notice}</div>}
      <section className="price-table-wrap"><div className="price-table-head"><span>POSTE DE DÉPENSE</span><span>ORIGINE</span><span>PRIX UNITAIRE</span><span>ACTION</span></div>{loading ? <div className="loading-row"><span className="loader" />Chargement des prix...</div> : filtered.length ? filtered.map((price) => <div className="price-row" key={price.key}><div className="price-name"><strong>{price.label}</strong><small>{price.key}</small></div><span className={`price-source source-${price.source}`}>{price.source === "user" ? "Personnel" : price.source === "city" ? "Ville" : "Indicatif"}</span><label className="price-input"><span className="sr-only">Prix {price.label}</span><input type="number" min="0" step="1" value={values[price.key] ?? price.value} onChange={(event) => setValues({ ...values, [price.key]: event.target.value })} /><small>{price.unit === "%" ? "%" : "FCFA"}{price.unit !== "%" && ` / ${price.unit}`}</small></label><button className="text-button price-save" onClick={() => savePrice(price)}>{user.role === "admin" ? "Prix ville" : "Enregistrer"}<ArrowRight size={14} /></button></div>) : <div className="empty-state compact-empty"><p>Aucun poste ne correspond à cette recherche.</p></div>}</section>
      <div className="price-footnote"><ShieldCheck size={17} /><p>{user.role === "admin" ? "Vos modifications sont visibles par tous les comptes pour la ville sélectionnée." : "Vos ajustements personnels restent privés et sont prioritaires dans vos devis."} Les prix sont indicatifs et doivent être confirmés auprès des fournisseurs.</p></div>
    </>
  );
}

function SharedPage() {
  const { token = "" } = useParams();
  const [shared, setShared] = useState<{ lecture_seule: boolean; projet: { nom: string; ville: string; type: string }; analyse: Analysis; metre: Quantities["metre"]; devis?: Quantities["devis"] } | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<{ lecture_seule: boolean; projet: { nom: string; ville: string; type: string }; analyse: Analysis; metre: Quantities["metre"]; devis?: Quantities["devis"] }>(`/shared/${token}`).then(setShared).catch((caught) => setError(errorText(caught))).finally(() => setLoading(false));
  }, [token]);

  return <main className="shared-layout"><header className="shared-header"><Link to="/" className="brand"><span className="brand-mark"><Building2 size={20} /></span><span>GéoCivil<span className="brand-period">.</span></span></Link><span className="readonly-tag"><ShieldCheck size={15} />Lecture seule</span></header>{loading ? <div className="loading-row"><span className="loader" />Chargement de l’étude...</div> : !shared ? <div className="shared-error"><div className="empty-icon"><X size={24} /></div><span className="eyebrow">LIEN INDISPONIBLE</span><h1>Cette étude n’est plus accessible.</h1><p>{error || "Le lien a expiré ou a été révoqué."}</p><Link className="button button-primary" to="/">Accéder à GéoCivil<ArrowRight size={16} /></Link></div> : <div className="shared-content"><span className="eyebrow">ÉTUDE PARTAGÉE · {shared.analyse.version_moteur || "BAEL"}</span><h1>{shared.projet.nom}</h1><p className="shared-subtitle"><MapPin size={16} />{shared.projet.ville}<span>·</span>Maison individuelle</p><div className="shared-verdict"><span className="verdict-icon"><Check size={20} /></span><div><span className="eyebrow">PRÉ-DIMENSIONNEMENT</span><h2>{shared.analyse.verdict?.texte || "Analyse calculée"}</h2><p>Référentiel BAEL 91 modifié 99 · Résultat fourni à titre indicatif</p></div></div><div className="analysis-metrics"><div><span>Pression moyenne du sol</span><strong>{shared.analyse.verdict?.pression_moyenne_kPa ?? "—"}<small> kPa</small></strong></div><div><span>Fondations retenues</span><strong className="metric-text">{shared.analyse.fondations?.type_retenu || "—"}</strong></div><div><span>Surface bâtie</span><strong>{formatMoney(shared.metre.ratios.surface_batie_m2)}<small> m²</small></strong></div></div>{shared.devis && <div className="shared-estimate"><span>ESTIMATION INDICATIVE</span><strong>{formatMoney(shared.devis.total_FCFA)} <small>FCFA</small></strong></div>}{!!shared.analyse.alertes?.length && <div className="alert-list">{shared.analyse.alertes.map((alert) => <p key={alert}><span>!</span>{alert}</p>)}</div>}<div className="technical-disclaimer"><ShieldCheck size={17} /><p>Cette étude partagée ne constitue pas un plan d’exécution. Les résultats doivent être validés par un ingénieur agréé.</p></div></div>}<footer className="shared-footer">GéoCivil · Étude structurelle préliminaire</footer></main>;
}

export default App;