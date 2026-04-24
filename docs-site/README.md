# Warehouse 3PL — Docs Site

An **alternate** documentation site for the Warehouse 3PL Frappe app. It
covers the same material as the original VitePress site but is built with
**Astro Starlight** for a deliberately different look and feel.

- Framework: [Astro](https://astro.build) + [Starlight](https://starlight.astro.build)
- Styling: custom teal accent (see `src/styles/custom.css`)
- Deploys: [Vercel](https://vercel.com) (zero-config, root = `docs-site/`)
- Lives inside: `apps/warehouse_3pl/docs-site/`

## Local development

```bash
cd docs-site
npm install
npm run dev
# open http://localhost:4321
```

## Build

```bash
npm run build
npm run preview
```

Build output: `dist/`.

## Deploy to Vercel

1. Import `https://github.com/sivajyothis7/warehouse_3pl` into Vercel.
2. In **Project Settings → General**, set:
   - **Root Directory** → `docs-site`
   - **Framework Preset** → Astro (auto-detected)
3. Deploy. No env vars needed.

Every push to `develop` triggers a redeploy.

## Content layout

```
src/content/docs/
├── index.mdx                    # Splash / hero
├── getting-started.md
├── installation.md
├── user/                        # User Guide
│   ├── overview.md
│   ├── inbound.md
│   ├── outbound.md
│   ├── warehouse-job.md
│   └── billing.md
├── guide/                       # Developer Guide
│   ├── architecture.md
│   ├── doctypes.md
│   ├── end-to-end-flow.md
│   ├── engines.md
│   └── customisation.md
└── reference/                   # Reference
    ├── master-data.md
    ├── policy-engine.md
    ├── billing.md
    └── custom-fields.md
```

Sidebar ordering and labels are controlled in `astro.config.mjs`.

## Notes

- Mermaid code blocks currently render as preformatted text. To render
  them as diagrams, add a remark/rehype Mermaid plugin or a small
  client-side Mermaid component — kept out for now to keep the build
  simple and fast.
- Edit links point to the `develop` branch on GitHub. Adjust the
  `editLink.baseUrl` in `astro.config.mjs` if you branch off.
