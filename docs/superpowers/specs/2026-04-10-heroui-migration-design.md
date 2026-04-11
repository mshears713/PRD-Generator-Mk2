# HeroUI v3 Migration Design

**Date:** 2026-04-10
**Branch:** heroui-cli
**Scope:** Drop-in component replacement — same layout, same logic, new component primitives

---

## Summary

Replace all hand-rolled CSS and custom UI primitives in CodeGarden's frontend with HeroUI v3 (beta) components and Tailwind v4 utility classes. No layout restructuring, no logic changes. The goal is to validate HeroUI v3 as the component foundation before any further UI work.

---

## Decisions

| Decision | Choice | Reason |
|---|---|---|
| Migration scope | Drop-in replacement | Safest first pass; validates HeroUI without risk |
| Theme | HeroUI default dark | Zinc darks + violet accent are close enough to current palette; no custom theme needed |
| CSS strategy | Full handoff — delete `main.css` | Tailwind v4 is installed anyway; keep everything in one system |
| Interactive patterns | Hybrid — HeroUI semantic where free, primitive swap elsewhere | `ToggleButtonGroup` for segmented/chip controls; `DisclosureGroup` for growth check; `Card`/`Button` everywhere else |

---

## Setup Changes

### Packages
```
npm i @heroui/react @heroui/styles
```

### `index.html`
Add dark theme attributes to `<html>` and class to `<body>`:
```html
<html class="dark" data-theme="dark">
  <body class="bg-background text-foreground">
```

### CSS
Delete `src/styles/main.css`. Create `src/styles/globals.css`:
```css
@import "tailwindcss";
@import "@heroui/styles";

/* Markdown body — no HeroUI equivalent */
.markdown-body h1, .markdown-body h2, .markdown-body h3 { ... }
.markdown-body table, .markdown-body code, .markdown-body pre { ... }
```

### `src/main.jsx`
Update import: `./styles/main.css` → `./styles/globals.css`

---

## Component Mapping

### App.jsx
| Current | Replacement |
|---|---|
| `.app` wrapper div | Tailwind: `max-w-[1100px] mx-auto px-6 py-8 pb-16` |
| `.app-header` h1 gradient | Tailwind: `bg-gradient-to-br from-accent to-violet-400 bg-clip-text text-transparent` |
| `.error-banner` | `<Alert color="danger">` |

### IdeaInput.jsx
| Current | Replacement |
|---|---|
| `.idea-card` | `<Card><Card.Body>` |
| `<textarea>` | `<TextArea label="Describe your idea">` |
| `.btn-primary` | `<Button color="accent" fullWidth>` |

### LoadingState.jsx
| Current | Replacement |
|---|---|
| `.spinner` (custom CSS keyframe) | `<Spinner color="accent">` |
| `.loading-state` wrapper | Tailwind: `flex flex-col items-center py-16 gap-4` |

### QuickSetupPanel.jsx
| Current | Replacement |
|---|---|
| `SegmentedControl` component | `<ToggleButtonGroup selectionMode="single">` + `<ToggleButton>` |
| `ChipGroup` (single-select) | `<ToggleButtonGroup selectionMode="single">` + `<ToggleButton>` |
| `ChipGroup` (multi-select) | `<ToggleButtonGroup selectionMode="multiple">` + `<ToggleButton>` |
| `.qs-block` sections | Tailwind-styled bordered divs (structure preserved) |
| `.btn-primary` Continue | `<Button color="accent" fullWidth>` |

### RecommendationPanel.jsx
| Current | Replacement |
|---|---|
| `.summary-card` | `<Card><Card.Body>` |
| `.system-type-tag` | `<Chip size="sm" color="accent" variant="soft">` |
| `.insight-grid` / `.insight-grid-3` | Tailwind: `grid grid-cols-1 md:grid-cols-3 gap-4` |
| `.rationale-grid` / `.rationale-row` | Tailwind: `grid grid-cols-[72px_1fr] gap-3` |
| `.btn-primary` Generate | `<Button color="accent" fullWidth>` |

### SelectionCards.jsx + DeploymentRow.jsx
| Current | Replacement |
|---|---|
| `.card-btn` (single-select) | `<ToggleButton>` inside `<ToggleButtonGroup selectionMode="single">` |
| `.card-btn-recommended` + `.card-rec-badge` | `<Chip size="sm" color="accent">` inside button label |
| `.card-btn-sponsored` + `.card-sponsored-star` | `<Chip size="sm" color="warning">` inside button label |
| `.api-key-input` `<input>` | `<Input type="text">` |

### DecisionCard.jsx
| Current | Replacement |
|---|---|
| `.decision-card` | `<Card>` with Tailwind border overrides for recommended/sponsored states |
| `.sponsored-badge` | `<Chip color="warning" variant="flat">` |
| `.dc-columns` 2-col grid | Tailwind: `grid grid-cols-2 gap-3` |
| Learn more `<a>` | `<Link isExternal>` |

### OutputPanel.jsx
| Current | Replacement |
|---|---|
| `.output-section` | `<Card><Card.Body>` |
| `.copy-btn` | `<Button variant="bordered" size="sm">` |
| Growth check expand/collapse items | `<DisclosureGroup>` (one per Good / Warnings / Missing column) |
| `.env-block` `<pre>` | Tailwind: `bg-background border border-border rounded-lg p-4 font-mono text-sm overflow-x-auto` |
| `.btn-secondary` Start Over | `<Button variant="bordered">` |

---

## Implementation Order

Files are migrated one at a time, dev server hot-reloads after each:

1. Install packages + create `globals.css` + update `index.html`
2. `LoadingState.jsx` — simplest, self-contained
3. `IdeaInput.jsx` — one card + textarea + button
4. `QuickSetupPanel.jsx` — ToggleButtonGroup migration (replaces both SegmentedControl and ChipGroup)
5. `DecisionCard.jsx` — Card + Chip + Link (used by SelectionCards and DeploymentRow)
6. `SelectionCards.jsx` + `DeploymentRow.jsx` — ToggleButtonGroup for card-btn pattern
7. `RecommendationPanel.jsx` — layout Tailwind + Card wrappers
8. `OutputPanel.jsx` — Card sections + DisclosureGroup for growth check
9. `App.jsx` — header gradient + Alert for errors
10. Delete `main.css`, verify nothing broken

---

## What Does Not Change

- All component props and interfaces
- All state management in `App.jsx`
- All API calls (`/recommend`, `/generate`)
- All data in `src/data/options.js`
- `react-markdown` for PRD rendering
- The markdown CSS block (kept in `globals.css`)
