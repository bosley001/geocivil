# GéoCivil – API (étape 1 : socle)

FastAPI + PostgreSQL. Comptes (email + mot de passe, JWT), projets maison R+0 à R+2,
prix par ville (admin) avec ajustement par utilisateur. Normes visées : BAEL.

## Lancer en local
    cp .env.example .env        # puis éditer SECRET_KEY et ADMIN_EMAIL
    docker compose up --build   # API sur http://localhost:8000/docs

Dans un second terminal, lancer l’interface :
    cd frontend && npm ci && npm run dev

L’application est alors disponible sur http://localhost:5173. Elle utilise
`VITE_API_URL` pour joindre l’API (par défaut `http://localhost:8000`). Pour
un autre environnement, définir cette variable avant le build.

## Tests
    cd backend && python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
    .venv/bin/python -m pytest -q

## Déployer sur Render
Pousser le dépôt sur GitHub, puis Render > New > Blueprint en sélectionnant le
dossier racine du dépôt. Le Blueprint crée l’API et le frontend statique. Renseigner
`ADMIN_EMAIL` ; les services `geocivil-api-v2`, `geocivil-db-v2` et
`geocivil-frontend-v2` sont indépendants des anciens services. Le frontend cible
`https://geocivil-api-v2.onrender.com` et l’API autorise
`https://geocivil-frontend-v2.onrender.com`. Le compte créé avec `ADMIN_EMAIL`
devient admin. La nouvelle base est vide et ne reprend pas les données précédentes.

## Principaux endpoints
POST /auth/register, /auth/login · GET /auth/me · CRUD /projects ·
GET /prices?city= · PUT/DELETE /prices/overrides · PUT /admin/prices · POST /admin/price-items

## Moteur BAEL (étape 2)
POST /projects/{id}/analysis calcule et enregistre dalles, poutres, poteaux, semelles (ferraillage + ELS, flèche, fissuration, poinçonnement) ; GET renvoie la dernière analyse. Hypothèses listées dans la réponse.

## Métrés et devis (étape 3)
GET /projects/{id}/quantities : métré par ouvrage, matériaux à acheter, devis en FCFA (prix : défaut → ville → ajustement utilisateur).
GET /projects/{id}/export/devis.xlsx : classeur Excel avec formules (prix et pourcentages modifiables en bleu).
Les nouveaux postes de prix sont ajoutés automatiquement au démarrage.

## Rapports et partage (étape 4)
GET /projects/{id}/report.pdf?prices=true|false · GET /projects/{id}/plans/{implantation|details}.svg
POST/GET /projects/{id}/shares, DELETE /projects/{id}/shares/{sid} : liens en lecture seule (jeton affiché une fois, stocké haché, expiration, révocation, prix optionnels).
Public : GET /shared/{token}, /shared/{token}/report.pdf, /shared/{token}/plans/{name}.svg (limités en débit).

## Prochaine étape
Interface React en français (étape 5) : connexion, tableau de bord, formulaire projet, résultats, devis, partage, admin des prix.
