# HeroUI v3 Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all hand-rolled CSS and custom UI primitives in CodeGarden's frontend with HeroUI v3 components and Tailwind v4 utility classes, one component file at a time.

**Architecture:** Drop-in swap — same component interfaces, same App.jsx stage logic, same API calls. HeroUI default dark theme (zinc/violet). `main.css` deleted entirely; structural layout uses Tailwind inline classes; markdown styles kept in a minimal `globals.css` block.

**Tech Stack:** React 19, Vite 8, HeroUI v3 (`@heroui/react` + `@heroui/styles`), Tailwind CSS v4

---

## File Map

| File | Action |
|---|---|
| `frontend/package.json` | Add `@heroui/react`, `@heroui/styles` |
| `frontend/index.html` | Add `class="dark" data-theme="dark"` to `<html>`, `class="bg-background text-foreground"` to `<body>` |
| `frontend/src/styles/main.css` | **Delete** |
| `frontend/src/styles/globals.css` | **Create** — Tailwind + HeroUI imports + markdown styles |
| `frontend/src/main.jsx` | Update CSS import path |
| `frontend/src/components/LoadingState.jsx` | Replace spinner div with `<Spinner>` |
| `frontend/src/components/IdeaInput.jsx` | Replace card/textarea/button with `Card`, `TextArea`, `Button` |
| `frontend/src/components/QuickSetupPanel.jsx` | Replace `SegmentedControl` + `ChipGroup` with `ToggleButtonGroup` |
| `frontend/src/components/DecisionCard.jsx` | Replace div/badge/link with `Card`, `Chip`, `Link` |
| `frontend/src/components/SelectionCards.jsx` | Replace card-btn pattern with HeroUI `Button` (selected via variant) |
| `frontend/src/components/DeploymentRow.jsx` | Same card-btn → Button pattern as SelectionCards |
| `frontend/src/components/RecommendationPanel.jsx` | Replace summary-card divs + layout with `Card` + Tailwind grid |
| `frontend/src/components/OutputPanel.jsx` | Replace output-section with `Card`, growth items with `Disclosure`, copy btn with `Button` |
| `frontend/src/App.jsx` | Replace error-banner with `Alert`, header gradient with Tailwind, wrapper with Tailwind |

---

## Task 1: Install HeroUI and create globals.css

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/index.html`
- Create: `frontend/src/styles/globals.css`
- Modify: `frontend/src/main.jsx`
- Delete: `frontend/src/styles/main.css`

- [ ] **Step 1: Install packages**

Run in `frontend/`:
```bash
npm install @heroui/react @heroui/styles
```
Expected: packages added to `node_modules`, `package.json` updated.

- [ ] **Step 2: Update index.html**

Open `frontend/index.html`. Find the `<html>` tag and `<body>` tag and update them:
```html
<html lang="en" class="dark" data-theme="dark">
  ...
  <body class="bg-background text-foreground">
```

- [ ] **Step 3: Create globals.css**

Create `frontend/src/styles/globals.css` with this exact content:
```css
@import "tailwindcss";
@import "@heroui/styles";

/* Markdown body — rendered by react-markdown, no HeroUI equivalent */
.markdown-body h1,
.markdown-body h2,
.markdown-body h3 {
  color: var(--foreground);
  font-weight: 600;
  margin: 1rem 0 0.5rem;
}
.markdown-body h1 { font-size: 1.35rem; }
.markdown-body h2 {
  font-size: 1.05rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.25rem;
}
.markdown-body h3 { font-size: 0.95rem; }
.markdown-body p { margin: 0.5rem 0; }
.markdown-body ul,
.markdown-body ol { padding-left: 1.5rem; margin: 0.4rem 0; }
.markdown-body li { margin: 0.2rem 0; }
.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.75rem 0;
  font-size: 0.83rem;
}
.markdown-body th,
.markdown-body td {
  border: 1px solid var(--border);
  padding: 0.4rem 0.75rem;
  text-align: left;
}
.markdown-body th { background: var(--background); font-weight: 600; }
.markdown-body code {
  background: var(--background);
  padding: 0.1em 0.3em;
  border-radius: 3px;
  font-size: 0.84em;
  font-family: monospace;
}
.markdown-body pre {
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.75rem;
  overflow-x: auto;
  margin: 0.5rem 0;
}
.markdown-body pre code { background: none; padding: 0; }
.markdown-body strong { font-weight: 600; }
```

- [ ] **Step 4: Update main.jsx import**

Open `frontend/src/main.jsx`. Change:
```js
import './styles/main.css'
```
to:
```js
import './styles/globals.css'
```

- [ ] **Step 5: Delete main.css**

Delete the file `frontend/src/styles/main.css`.

- [ ] **Step 6: Verify dev server starts**

The dev server should already be running at `http://localhost:5173`. Check it still loads without errors (the page will look broken — no styles yet — that's expected).

- [ ] **Step 7: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/index.html frontend/src/styles/globals.css frontend/src/main.jsx
git commit -m "feat: install HeroUI v3, replace main.css with globals.css"
```

---

## Task 2: LoadingState.jsx

**Files:**
- Modify: `frontend/src/components/LoadingState.jsx`

- [ ] **Step 1: Replace the component**

Replace the entire contents of `frontend/src/components/LoadingState.jsx` with:
```jsx
import { useState, useEffect } from 'react'
import { Spinner } from '@heroui/react'

export default function LoadingState({ message, stages, cycleInterval = 6000 }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (!stages) return
    const timer = setInterval(
      () => setIndex(i => Math.min(i + 1, stages.length - 1)),
      cycleInterval
    )
    return () => clearInterval(timer)
  }, [stages, cycleInterval])

  return (
    <div className="flex flex-col items-center py-16 gap-4">
      <Spinner color="accent" />
      <p className="text-muted text-sm">{stages ? stages[index] : message}</p>
    </div>
  )
}
```

- [ ] **Step 2: Verify in browser**

Trigger the loading state by submitting an idea. The spinner should appear styled correctly.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/LoadingState.jsx
git commit -m "feat: replace custom spinner with HeroUI Spinner in LoadingState"
```

---

## Task 3: IdeaInput.jsx

**Files:**
- Modify: `frontend/src/components/IdeaInput.jsx`

- [ ] **Step 1: Replace the component**

Replace the entire contents of `frontend/src/components/IdeaInput.jsx` with:
```jsx
import { Button, Card, TextArea } from '@heroui/react'

export default function IdeaInput({ idea, onChange, onSubmit }) {
  function handleKey(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') onSubmit()
  }

  return (
    <div className="flex justify-center">
      <Card className="w-full">
        <Card.Content className="flex flex-col gap-3 p-6">
          <TextArea
            aria-label="Describe your idea"
            placeholder="e.g. A task manager for remote teams with real-time updates and role-based access..."
            value={idea}
            rows={5}
            onChange={e => onChange(e.target.value)}
            onKeyDown={handleKey}
            autoFocus
          />
          <p className="text-muted text-xs">Tip: Ctrl+Enter to submit</p>
          <Button
            variant="primary"
            className="w-full"
            onPress={onSubmit}
            isDisabled={!idea.trim()}
          >
            Understand My Idea →
          </Button>
        </Card.Content>
      </Card>
    </div>
  )
}
```

- [ ] **Step 2: Verify in browser**

The idea input stage should show a HeroUI card with a textarea and primary button.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/IdeaInput.jsx
git commit -m "feat: migrate IdeaInput to HeroUI Card, TextArea, Button"
```

---

## Task 4: QuickSetupPanel.jsx

**Files:**
- Modify: `frontend/src/components/QuickSetupPanel.jsx`

The current `SegmentedControl` and `ChipGroup` custom components are replaced with HeroUI's `ToggleButtonGroup`. Key API notes:
- `selectedKeys={new Set([value])}` for single-select (value is a string)
- `selectedKeys={new Set(value)}` for multi-select (value is an array)
- `onSelectionChange` receives a `Set<Key>` — extract with `[...keys][0]` for single, `[...keys]` for multi
- Each `ToggleButton` needs a unique `id` prop
- Add `<ToggleButtonGroup.Separator />` before the content of every button after the first, for the segmented divider look

- [ ] **Step 1: Replace the component**

Replace the entire contents of `frontend/src/components/QuickSetupPanel.jsx` with:
```jsx
import { useState } from 'react'
import { Button, ToggleButton, ToggleButtonGroup } from '@heroui/react'

const DEFAULT_CONSTRAINTS = {
  user_scale: 'small',
  auth: 'none',
  data: { types: [], persistence: 'temporary' },
  execution: 'short',
  app_shape: 'simple',
}

export default function QuickSetupPanel({ onContinue }) {
  const [c, setC] = useState(DEFAULT_CONSTRAINTS)

  function set(key, value) {
    setC(prev => ({ ...prev, [key]: value }))
  }

  function setData(key, value) {
    setC(prev => ({ ...prev, data: { ...prev.data, [key]: value } }))
  }

  function handleSingle(setter) {
    return (keys) => {
      const val = [...keys][0]
      if (val) setter(val)
    }
  }

  function handleMulti(setter) {
    return (keys) => setter([...keys])
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="text-center">
        <p className="font-semibold text-foreground">Quick Setup</p>
        <p className="text-muted text-sm mt-1">5 questions · ~15 seconds</p>
      </div>

      <div className="flex flex-col">

        {/* 1. Users & Scale */}
        <div className="bg-surface border border-border rounded-t-lg border-b-0 p-4">
          <p className="text-muted text-xs font-bold uppercase tracking-widest mb-3">Who's using this?</p>
          <ToggleButtonGroup
            selectionMode="single"
            selectedKeys={new Set([c.user_scale])}
            onSelectionChange={handleSingle(v => set('user_scale', v))}
            size="sm"
          >
            <ToggleButton id="single">Just me</ToggleButton>
            <ToggleButton id="small"><ToggleButtonGroup.Separator />Small group</ToggleButton>
            <ToggleButton id="large"><ToggleButtonGroup.Separator />Larger audience</ToggleButton>
          </ToggleButtonGroup>
        </div>

        {/* 2. Accounts / Identity */}
        <div className="bg-surface border border-border border-b-0 p-4">
          <p className="text-muted text-xs font-bold uppercase tracking-widest mb-3">Accounts / login?</p>
          <ToggleButtonGroup
            selectionMode="single"
            selectedKeys={new Set([c.auth])}
            onSelectionChange={handleSingle(v => set('auth', v))}
            size="sm"
          >
            <ToggleButton id="none">No accounts</ToggleButton>
            <ToggleButton id="simple"><ToggleButtonGroup.Separator />Email / magic link</ToggleButton>
            <ToggleButton id="oauth"><ToggleButtonGroup.Separator />Social login</ToggleButton>
          </ToggleButtonGroup>
        </div>

        {/* 3. Data & Storage */}
        <div className="bg-surface border border-border border-b-0 p-4">
          <p className="text-muted text-xs font-bold uppercase tracking-widest mb-3">What data does it handle?</p>
          <ToggleButtonGroup
            selectionMode="multiple"
            selectedKeys={new Set(c.data.types)}
            onSelectionChange={handleMulti(v => setData('types', v))}
            size="sm"
            className="flex-wrap"
          >
            <ToggleButton id="none">No storage</ToggleButton>
            <ToggleButton id="text"><ToggleButtonGroup.Separator />Text / data</ToggleButton>
            <ToggleButton id="files"><ToggleButtonGroup.Separator />Files (PDFs, images)</ToggleButton>
            <ToggleButton id="results"><ToggleButtonGroup.Separator />Saved history</ToggleButton>
          </ToggleButtonGroup>
          <div className="flex items-center gap-3 mt-3 flex-wrap">
            <span className="text-muted text-sm whitespace-nowrap">Save long-term?</span>
            <ToggleButtonGroup
              selectionMode="single"
              selectedKeys={new Set([c.data.persistence])}
              onSelectionChange={handleSingle(v => setData('persistence', v))}
              size="sm"
            >
              <ToggleButton id="temporary">Temporary</ToggleButton>
              <ToggleButton id="permanent"><ToggleButtonGroup.Separator />Persistent</ToggleButton>
            </ToggleButtonGroup>
          </div>
        </div>

        {/* 4. Speed / Execution */}
        <div className="bg-surface border border-border border-b-0 p-4">
          <p className="text-muted text-xs font-bold uppercase tracking-widest mb-3">How fast does it need to respond?</p>
          <ToggleButtonGroup
            selectionMode="single"
            selectedKeys={new Set([c.execution])}
            onSelectionChange={handleSingle(v => set('execution', v))}
            size="sm"
          >
            <ToggleButton id="realtime">Instant</ToggleButton>
            <ToggleButton id="short"><ToggleButtonGroup.Separator />Few seconds</ToggleButton>
            <ToggleButton id="async"><ToggleButtonGroup.Separator />Background</ToggleButton>
          </ToggleButtonGroup>
        </div>

        {/* 5. App Shape */}
        <div className="bg-surface border border-border rounded-b-lg p-4">
          <p className="text-muted text-xs font-bold uppercase tracking-widest mb-3">What shape is this app?</p>
          <ToggleButtonGroup
            selectionMode="single"
            selectedKeys={new Set([c.app_shape])}
            onSelectionChange={handleSingle(v => set('app_shape', v))}
            size="sm"
          >
            <ToggleButton id="simple">Simple tool</ToggleButton>
            <ToggleButton id="ai_core"><ToggleButtonGroup.Separator />AI-powered tool</ToggleButton>
            <ToggleButton id="workflow"><ToggleButtonGroup.Separator />Multi-step workflow</ToggleButton>
          </ToggleButtonGroup>
        </div>

      </div>

      <Button variant="primary" className="w-full" onPress={() => onContinue(c)}>
        Continue →
      </Button>
    </div>
  )
}
```

- [ ] **Step 2: Verify in browser**

Navigate to the Quick Setup stage. All five questions should render with working toggle groups. Clicking an option should visually select it. The data types question should allow multi-select.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/QuickSetupPanel.jsx
git commit -m "feat: replace SegmentedControl/ChipGroup with HeroUI ToggleButtonGroup"
```

---

## Task 5: DecisionCard.jsx

**Files:**
- Modify: `frontend/src/components/DecisionCard.jsx`

- [ ] **Step 1: Replace the component**

Replace the entire contents of `frontend/src/components/DecisionCard.jsx` with:
```jsx
import { Card, Chip, Link } from '@heroui/react'

function SponsoredBadge() {
  return <Chip size="sm" color="warning" variant="soft">✦ Sponsored</Chip>
}

export default function DecisionCard({
  title,
  subtitle,
  reason,
  learnMoreUrl,
  benefits = [],
  drawbacks = [],
  sponsored = false,
  sponsorOffer = '',
  isRecommended = false,
}) {
  const borderClass = sponsored
    ? 'border border-warning/55'
    : isRecommended
    ? 'border border-accent/70'
    : ''

  return (
    <Card className={`mt-2 ${borderClass}`}>
      <Card.Content className="p-4 flex flex-col gap-2">

        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-col gap-0.5">
            <span className="text-sm font-semibold text-foreground">{title}</span>
            <span className="text-xs text-muted">{subtitle}</span>
          </div>
          {sponsored && <SponsoredBadge />}
        </div>

        {reason && (
          <p className="text-xs text-muted italic leading-relaxed">{reason}</p>
        )}

        {sponsored && sponsorOffer && (
          <div className="bg-accent/8 border border-accent/20 rounded-md px-3 py-2 text-xs text-foreground leading-relaxed">
            {sponsorOffer}
          </div>
        )}

        <div className="grid grid-cols-2 gap-3 mt-1">
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-success mb-1.5">✅ Benefits</p>
            <ul className="flex flex-col gap-1">
              {benefits.map((b, i) => (
                <li key={i} className="text-xs text-muted leading-relaxed">{b}</li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-danger mb-1.5">❌ Drawbacks</p>
            <ul className="flex flex-col gap-1">
              {drawbacks.map((d, i) => (
                <li key={i} className="text-xs text-muted leading-relaxed">{d}</li>
              ))}
            </ul>
          </div>
        </div>

        {learnMoreUrl && (
          <Link
            href={learnMoreUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-muted mt-1 self-start"
          >
            Learn more
            <Link.Icon />
          </Link>
        )}

      </Card.Content>
    </Card>
  )
}
```

- [ ] **Step 2: Verify in browser**

Navigate to the recommendation stage, select a stack option (e.g. FastAPI). The DecisionCard should appear below the button row with title, subtitle, benefits/drawbacks columns, and optional learn more link.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/DecisionCard.jsx
git commit -m "feat: migrate DecisionCard to HeroUI Card, Chip, Link"
```

---

## Task 6: SelectionCards.jsx

**Files:**
- Modify: `frontend/src/components/SelectionCards.jsx`

The `card-btn` button pattern (pill-shaped, flex-wrap, individually separated) maps to HeroUI `Button` with `variant="secondary"` when selected and `variant="outline"` when not. This keeps the buttons visually separated (unlike ToggleButtonGroup which creates an attached segmented control).

- [ ] **Step 1: Replace the component**

Replace the entire contents of `frontend/src/components/SelectionCards.jsx` with:
```jsx
import { Button, Chip, Input } from '@heroui/react'
import DecisionCard from './DecisionCard'
import { STACK_DETAILS, API_DETAILS } from '../data/options'

const OPTIONS = {
  scope: ['frontend', 'backend', 'fullstack'],
  backend: ['fastapi', 'node', 'none'],
  frontend: ['react', 'static', 'none'],
  apis: ['openrouter', 'tavily'],
  database: ['postgres', 'firebase', 'none'],
}

const LABELS = {
  scope: 'Scope',
  backend: 'Backend',
  frontend: 'Frontend',
  apis: 'APIs (multi-select)',
  database: 'Database',
}

function resolveDetail(field, value, architectureData) {
  if (!value) return null
  const staticDetail = STACK_DETAILS[field]?.[value]
  if (!staticDetail) return null
  const backendOption = architectureData?.[field]?.options?.[value]
  return {
    name: staticDetail.name,
    subtitle: staticDetail.subtitle,
    learnMoreUrl: staticDetail.learnMoreUrl || null,
    reason: backendOption?.reason || null,
    benefits: backendOption?.benefits?.length ? backendOption.benefits : staticDetail.benefits,
    drawbacks: backendOption?.drawbacks?.length ? backendOption.drawbacks : staticDetail.drawbacks,
  }
}

function StackGroup({ field, selections, onSelect, architectureData }) {
  const selected = selections[field]
  const recommended = architectureData?.[field]?.recommended
  const detail = resolveDetail(field, selected, architectureData)

  const visibleOptions = OPTIONS[field].filter(opt => {
    const optData = architectureData?.[field]?.options?.[opt]
    return !optData || optData.relevant !== false
  })

  return (
    <div className="flex flex-col gap-2">
      <label className="text-xs font-bold uppercase tracking-wide text-muted">
        {LABELS[field]}
      </label>
      <div className="flex flex-wrap gap-2">
        {visibleOptions.map(opt => {
          const staticMeta = STACK_DETAILS[field]?.[opt]
          const isRec = opt === recommended
          const isSelected = selected === opt
          return (
            <Button
              key={opt}
              variant={isSelected ? 'secondary' : 'outline'}
              size="sm"
              onPress={() => onSelect(field, opt)}
              className="capitalize"
            >
              {staticMeta?.name || opt}
              {isRec && (
                <Chip size="sm" color="accent" className="ml-1 text-[10px]">★</Chip>
              )}
            </Button>
          )
        })}
      </div>
      {detail && selected && (
        <DecisionCard
          title={detail.name}
          subtitle={detail.subtitle}
          learnMoreUrl={detail.learnMoreUrl}
          reason={detail.reason}
          benefits={detail.benefits}
          drawbacks={detail.drawbacks}
          isRecommended={selected === recommended}
        />
      )}
    </div>
  )
}

export default function SelectionCards({ selections, onChange, architectureData }) {
  function selectSingle(field, value) {
    onChange({ ...selections, [field]: value })
  }

  function toggleApi(api) {
    const current = selections.apis || []
    const next = current.includes(api)
      ? current.filter(a => a !== api)
      : [...current, api]
    const api_keys = { ...selections.api_keys }
    if (!next.includes(api)) delete api_keys[api]
    onChange({ ...selections, apis: next, api_keys })
  }

  function setApiKey(api, value) {
    onChange({ ...selections, api_keys: { ...selections.api_keys, [api]: value } })
  }

  const selectedApis = selections.apis || []

  return (
    <div className="flex flex-col gap-6">

      {['scope', 'backend', 'frontend'].map(field => (
        <StackGroup
          key={field}
          field={field}
          selections={selections}
          onSelect={selectSingle}
          architectureData={architectureData}
        />
      ))}

      {/* APIs — multi-select */}
      <div className="flex flex-col gap-2">
        <label className="text-xs font-bold uppercase tracking-wide text-muted">
          {LABELS.apis}
        </label>
        <div className="flex flex-wrap gap-2">
          {OPTIONS.apis.map(api => {
            const meta = API_DETAILS[api]
            const isSelected = selectedApis.includes(api)
            return (
              <Button
                key={api}
                variant={isSelected ? 'secondary' : 'outline'}
                size="sm"
                onPress={() => toggleApi(api)}
                className={meta?.sponsored ? 'border-warning/55' : ''}
              >
                {meta?.name || api}
                {meta?.sponsored && (
                  <Chip size="sm" color="warning" className="ml-1 text-[10px]">✦</Chip>
                )}
              </Button>
            )
          })}
        </div>

        {selectedApis.map(api => {
          const meta = API_DETAILS[api]
          if (!meta) return null
          return (
            <DecisionCard
              key={api}
              title={meta.name}
              subtitle={meta.subtitle}
              learnMoreUrl={meta.learnMoreUrl}
              benefits={meta.benefits}
              drawbacks={meta.drawbacks}
              sponsored={meta.sponsored}
              sponsorOffer={meta.sponsorOffer}
            />
          )
        })}

        {selectedApis.map(api => (
          <div key={`key-${api}`} className="flex flex-col gap-1">
            <label className="text-xs text-muted capitalize">
              {API_DETAILS[api]?.name || api} API key
            </label>
            <Input
              type="text"
              placeholder={`Enter your ${API_DETAILS[api]?.name || api} key...`}
              value={selections.api_keys?.[api] || ''}
              onChange={e => setApiKey(api, e.target.value)}
              aria-label={`${API_DETAILS[api]?.name || api} API key`}
              className="max-w-sm font-mono"
            />
          </div>
        ))}
      </div>

      {/* Database */}
      <StackGroup
        field="database"
        selections={selections}
        onSelect={selectSingle}
        architectureData={architectureData}
      />

    </div>
  )
}
```

- [ ] **Step 2: Verify in browser**

On the recommendation stage, the Scope / Backend / Frontend / APIs / Database selectors should render as pill buttons. Clicking one selects it (secondary variant). A DecisionCard should expand below. API key inputs should appear for selected APIs.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/SelectionCards.jsx
git commit -m "feat: migrate SelectionCards card-btn pattern to HeroUI Button + Chip"
```

---

## Task 7: DeploymentRow.jsx

**Files:**
- Modify: `frontend/src/components/DeploymentRow.jsx`

Same pattern as SelectionCards — pill buttons with variant swap for selection, DecisionCard for the selected option.

- [ ] **Step 1: Replace the component**

Replace the entire contents of `frontend/src/components/DeploymentRow.jsx` with:
```jsx
import { Button, Chip } from '@heroui/react'
import DecisionCard from './DecisionCard'
import { DEPLOYMENT_OPTIONS } from '../data/options'

function getSponsorOffer(opt) {
  if (opt.sponsor_info) {
    const { why_use = [], bonus = '' } = opt.sponsor_info
    return [why_use[0], bonus].filter(Boolean).join(' — ')
  }
  return opt.sponsorOffer || ''
}

function mergeOption(backendOpt) {
  const staticOpt = DEPLOYMENT_OPTIONS.find(s => s.value === backendOpt.value) || {}
  return { ...staticOpt, ...backendOpt, subtitle: staticOpt.subtitle }
}

export default function DeploymentRow({ value, onChange, deploymentOptions }) {
  const options = deploymentOptions?.length
    ? deploymentOptions.map(mergeOption)
    : DEPLOYMENT_OPTIONS

  const selected = options.find(o => o.value === value)

  return (
    <div className="flex flex-col gap-2">
      <label className="text-xs font-bold uppercase tracking-wide text-muted">Deployment</label>
      <div className="flex flex-wrap gap-2">
        {options.map(opt => (
          <Button
            key={opt.value}
            variant={value === opt.value ? 'secondary' : 'outline'}
            size="sm"
            onPress={() => onChange(opt.value)}
            className={opt.sponsored ? 'border-warning/55' : ''}
          >
            {opt.name}
            {opt.sponsored && (
              <Chip size="sm" color="warning" className="ml-1 text-[10px]">✦</Chip>
            )}
          </Button>
        ))}
      </div>

      {selected && (
        <DecisionCard
          title={selected.name}
          subtitle={selected.subtitle}
          reason={selected.reason_for_recommendation}
          benefits={selected.benefits}
          drawbacks={selected.drawbacks}
          sponsored={selected.sponsored}
          sponsorOffer={getSponsorOffer(selected)}
          isRecommended={selected.recommended === true}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 2: Verify in browser**

Deployment row should render as pill buttons with the same selection behavior as the stack options.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/DeploymentRow.jsx
git commit -m "feat: migrate DeploymentRow card-btn pattern to HeroUI Button + Chip"
```

---

## Task 8: RecommendationPanel.jsx

**Files:**
- Modify: `frontend/src/components/RecommendationPanel.jsx`

Summary cards become `Card`, layout uses Tailwind grid classes, system type tag becomes `Chip`, `btn-primary` becomes `Button`.

- [ ] **Step 1: Replace the component**

Replace the entire contents of `frontend/src/components/RecommendationPanel.jsx` with:
```jsx
import { Button, Card, Chip } from '@heroui/react'
import SelectionCards from './SelectionCards'
import DeploymentRow from './DeploymentRow'

const RATIONALE_KEYS = ['scope', 'backend', 'frontend', 'apis', 'database']

export default function RecommendationPanel({
  summary, systemType, keyRequirements, rationale,
  coreSystemLogic, scopeBoundaries, phasedPlan,
  selections, onChange, architectureData,
  deployment, onDeploymentChange, deploymentOptions,
  onGenerate,
}) {
  const canGenerate = Boolean(
    selections.scope && selections.backend && selections.frontend && selections.database
  )

  return (
    <div className="flex flex-col gap-8">

      {/* 1. Overview */}
      <Card className="border border-accent/25">
        <Card.Content className="p-6">
          <div className="flex items-center gap-2 mb-2">
            <p className="text-xs font-bold uppercase tracking-widest text-accent">Overview</p>
            {systemType && (
              <Chip size="sm" color="accent" variant="soft">{systemType}</Chip>
            )}
          </div>
          <p className="text-foreground leading-relaxed">{summary}</p>
        </Card.Content>
      </Card>

      {/* 2. Core Logic + Key Requirements + Scope Boundaries */}
      {(coreSystemLogic || keyRequirements?.length > 0 || scopeBoundaries?.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {coreSystemLogic && (
            <Card>
              <Card.Content className="p-5">
                <p className="text-xs font-bold uppercase tracking-widest text-accent mb-2">Core Logic</p>
                <p className="text-foreground text-sm">{coreSystemLogic}</p>
              </Card.Content>
            </Card>
          )}
          {keyRequirements?.length > 0 && (
            <Card>
              <Card.Content className="p-5">
                <p className="text-xs font-bold uppercase tracking-widest text-accent mb-2">Key Requirements</p>
                <ul className="flex flex-col gap-1.5">
                  {keyRequirements.map((req, i) => (
                    <li key={i} className="text-sm text-foreground pl-3 relative before:content-['•'] before:absolute before:left-0 before:text-accent">
                      {req}
                    </li>
                  ))}
                </ul>
              </Card.Content>
            </Card>
          )}
          {scopeBoundaries?.length > 0 && (
            <Card>
              <Card.Content className="p-5">
                <p className="text-xs font-bold uppercase tracking-widest text-accent mb-2">Scope Boundaries</p>
                <ul className="flex flex-col gap-1.5">
                  {scopeBoundaries.map((b, i) => (
                    <li key={i} className="text-sm text-foreground pl-3 relative before:content-['•'] before:absolute before:left-0 before:text-accent">
                      {b}
                    </li>
                  ))}
                </ul>
              </Card.Content>
            </Card>
          )}
        </div>
      )}

      {/* 3. Why This Setup */}
      {rationale && (
        <Card>
          <Card.Content className="p-5">
            <p className="text-xs font-bold uppercase tracking-widest text-accent mb-3">Why This Setup</p>
            <div className="flex flex-col gap-2.5">
              {RATIONALE_KEYS.map(key => rationale[key] && (
                <div key={key} className="grid grid-cols-[72px_1fr] gap-3 items-baseline">
                  <span className="text-[11px] font-bold uppercase tracking-wide text-muted pt-0.5">{key}</span>
                  <span className="text-sm text-foreground leading-relaxed">{rationale[key]}</span>
                </div>
              ))}
            </div>
          </Card.Content>
        </Card>
      )}

      {/* 4. Recommended Setup */}
      <div>
        <h2 className="text-base font-semibold mb-4">
          Recommended Setup{' '}
          <span className="text-muted font-normal text-sm">(fully editable)</span>
        </h2>
        <SelectionCards selections={selections} onChange={onChange} architectureData={architectureData} />
      </div>

      {/* 5. Deployment */}
      <div>
        <h2 className="text-base font-semibold mb-4">Deployment</h2>
        <DeploymentRow value={deployment} onChange={onDeploymentChange} deploymentOptions={deploymentOptions} />
      </div>

      <Button
        variant="primary"
        className="w-full"
        onPress={onGenerate}
        isDisabled={!canGenerate}
      >
        Generate Blueprint →
      </Button>
    </div>
  )
}
```

- [ ] **Step 2: Verify in browser**

The recommendation stage should show: Overview card with system type chip, a 3-column insight grid, a Why This Setup card, the selection cards section, and deployment row, followed by the generate button.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/RecommendationPanel.jsx
git commit -m "feat: migrate RecommendationPanel to HeroUI Card, Chip, Button + Tailwind grid"
```

---

## Task 9: OutputPanel.jsx

**Files:**
- Modify: `frontend/src/components/OutputPanel.jsx`

Growth check expandable items become `Disclosure` components. Output sections become `Card`. Copy button and Start Over become `Button`.

- [ ] **Step 1: Replace the component**

Replace the entire contents of `frontend/src/components/OutputPanel.jsx` with:
```jsx
import { useState } from 'react'
import { Button, Card, Disclosure } from '@heroui/react'
import ReactMarkdown from 'react-markdown'

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)

  function copy() {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Button variant="outline" size="sm" onPress={copy}>
      {copied ? 'Copied!' : 'Copy'}
    </Button>
  )
}

const GROWTH_SECTIONS = [
  { key: 'good',     label: 'Good Choices',  topColor: 'border-t-2 border-t-success' },
  { key: 'warnings', label: 'Warnings',       topColor: 'border-t-2 border-t-warning' },
  { key: 'missing',  label: 'Still Missing',  topColor: 'border-t-2 border-t-danger' },
]

function GrowthCheckCards({ data }) {
  if (!data || typeof data !== 'object') return null

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {GROWTH_SECTIONS.map(({ key, label, topColor }) => (
        <Card key={key} className={topColor}>
          <Card.Content className="p-4">
            <p className="text-xs font-bold uppercase tracking-wide text-muted mb-3">{label}</p>
            <div className="flex flex-col gap-1">
              {(data[key] || []).map((item, i) => (
                <Disclosure key={i}>
                  <Disclosure.Heading>
                    <Disclosure.Trigger className="w-full flex justify-between items-center py-1.5 text-left text-sm font-medium text-foreground hover:text-accent transition-colors">
                      {item.title}
                      <Disclosure.Indicator className="text-muted text-xs flex-shrink-0" />
                    </Disclosure.Trigger>
                  </Disclosure.Heading>
                  <Disclosure.Content>
                    <Disclosure.Body className="text-xs text-muted leading-relaxed pt-1.5 pb-1 border-t border-border mt-0.5">
                      {item.detail}
                    </Disclosure.Body>
                  </Disclosure.Content>
                </Disclosure>
              ))}
            </div>
          </Card.Content>
        </Card>
      ))}
    </div>
  )
}

export default function OutputPanel({ output, onReset }) {
  return (
    <div className="flex flex-col gap-8">

      <Card>
        <Card.Content className="p-6">
          <h2 className="text-base font-semibold mb-4">Growth Check</h2>
          <GrowthCheckCards data={output.growth_check} />
        </Card.Content>
      </Card>

      <Card>
        <Card.Content className="p-6">
          <h2 className="text-base font-semibold mb-4">PRD</h2>
          <div className="markdown-body">
            <ReactMarkdown>{output.prd}</ReactMarkdown>
          </div>
        </Card.Content>
      </Card>

      <Card>
        <Card.Content className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold">.env</h2>
            <CopyButton text={output.env} />
          </div>
          <pre className="bg-background border border-border rounded-lg p-4 font-mono text-sm whitespace-pre-wrap overflow-x-auto text-foreground">
            {output.env}
          </pre>
        </Card.Content>
      </Card>

      <div className="flex justify-center">
        <Button variant="outline" onPress={onReset}>← Start Over</Button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify in browser**

Generate a full PRD. The output stage should show: Growth Check (3-column card grid with collapsible Disclosure items), PRD markdown, .env block with Copy button, and Start Over button.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/OutputPanel.jsx
git commit -m "feat: migrate OutputPanel to HeroUI Card, Disclosure, Button"
```

---

## Task 10: App.jsx + cleanup

**Files:**
- Modify: `frontend/src/App.jsx`

Replace the app wrapper div, header gradient, and error banner with Tailwind classes and HeroUI `Alert`.

- [ ] **Step 1: Replace App.jsx**

Replace the entire contents of `frontend/src/App.jsx` with:
```jsx
import { useState } from 'react'
import { Alert } from '@heroui/react'
import IdeaInput from './components/IdeaInput'
import LoadingState from './components/LoadingState'
import QuickSetupPanel from './components/QuickSetupPanel'
import RecommendationPanel from './components/RecommendationPanel'
import OutputPanel from './components/OutputPanel'

const GENERATE_STAGES = [
  'Normalizing system definition...',
  'Analyzing architecture...',
  'Generating PRD...',
  'Running Growth Check...',
]

export default function App() {
  const [stage, setStage] = useState('idea')
  const [idea, setIdea] = useState('')
  const [summary, setSummary] = useState('')
  const [systemType, setSystemType] = useState('')
  const [keyRequirements, setKeyRequirements] = useState([])
  const [rationale, setRationale] = useState(null)
  const [coreSystemLogic, setCoreSystemLogic] = useState('')
  const [scopeBoundaries, setScopeBoundaries] = useState([])
  const [phasedPlan, setPhasedPlan] = useState([])
  const [architectureData, setArchitectureData] = useState(null)
  const [deploymentOptions, setDeploymentOptions] = useState([])
  const [selections, setSelections] = useState({
    scope: '', backend: '', frontend: '', apis: [], database: '', api_keys: {},
  })
  const [deployment, setDeployment] = useState('render')
  const [output, setOutput] = useState(null)
  const [error, setError] = useState('')

  function handleUnderstand() {
    if (!idea.trim()) return
    setError('')
    setStage('quicksetup')
  }

  async function handleQuickSetupContinue(constraints) {
    setStage('recommending')
    setError('')
    try {
      const res = await fetch('/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea, constraints }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Request failed')
      const data = await res.json()
      setSummary(data.system_understanding || data.summary || '')
      setSystemType(data.system_type || '')
      setKeyRequirements(data.key_requirements || [])
      setRationale(data.rationale || null)
      setCoreSystemLogic(data.core_system_logic || '')
      setScopeBoundaries(data.scope_boundaries || [])
      setPhasedPlan(data.phased_plan || [])
      setArchitectureData(data.architecture || null)
      const depOpts = data.deployment || []
      setDeploymentOptions(depOpts)
      const recommended = depOpts.find(d => d.recommended)
      if (recommended) setDeployment(recommended.value)
      setSelections({ ...data.recommended, api_keys: {} })
      setStage('recommendation')
    } catch (e) {
      setError(e.message)
      setStage('quicksetup')
    }
  }

  async function handleGenerate() {
    setStage('generating')
    setError('')
    try {
      const res = await fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea, ...selections }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Request failed')
      const data = await res.json()
      setOutput(data)
      setStage('output')
    } catch (e) {
      setError(e.message)
      setStage('recommendation')
    }
  }

  function handleReset() {
    setStage('idea')
    setIdea('')
    setSummary('')
    setSystemType('')
    setKeyRequirements([])
    setRationale(null)
    setCoreSystemLogic('')
    setScopeBoundaries([])
    setPhasedPlan([])
    setArchitectureData(null)
    setDeploymentOptions([])
    setSelections({ scope: '', backend: '', frontend: '', apis: [], database: '', api_keys: {} })
    setDeployment('render')
    setOutput(null)
    setError('')
  }

  return (
    <div className="max-w-[1100px] mx-auto px-6 py-8 pb-16">
      <header className="text-center mb-12">
        <h1 className="text-4xl font-bold bg-gradient-to-br from-accent to-violet-400 bg-clip-text text-transparent">
          CodeGarden
        </h1>
        <p className="text-muted mt-1 text-base">Grow your idea into a build-ready blueprint</p>
      </header>

      {error && (
        <div className="mb-6">
          <Alert status="danger">
            <Alert.Indicator />
            <Alert.Content>
              <Alert.Description>{error}</Alert.Description>
            </Alert.Content>
          </Alert>
        </div>
      )}

      {stage === 'idea' && (
        <IdeaInput idea={idea} onChange={setIdea} onSubmit={handleUnderstand} />
      )}
      {stage === 'quicksetup' && (
        <QuickSetupPanel onContinue={handleQuickSetupContinue} />
      )}
      {stage === 'recommending' && (
        <LoadingState message="Analyzing your idea..." />
      )}
      {stage === 'recommendation' && (
        <RecommendationPanel
          summary={summary}
          systemType={systemType}
          keyRequirements={keyRequirements}
          rationale={rationale}
          coreSystemLogic={coreSystemLogic}
          scopeBoundaries={scopeBoundaries}
          phasedPlan={phasedPlan}
          selections={selections}
          onChange={setSelections}
          architectureData={architectureData}
          deployment={deployment}
          onDeploymentChange={setDeployment}
          deploymentOptions={deploymentOptions}
          onGenerate={handleGenerate}
        />
      )}
      {stage === 'generating' && (
        <LoadingState stages={GENERATE_STAGES} cycleInterval={6000} />
      )}
      {stage === 'output' && (
        <OutputPanel output={output} onReset={handleReset} />
      )}
    </div>
  )
}
```

- [ ] **Step 2: Verify full flow in browser**

Run through the complete flow:
1. Enter an idea → "Understand My Idea" button works
2. Quick Setup questions all toggle correctly
3. Recommendation stage renders all cards
4. Stack selection buttons work, DecisionCards appear
5. Generate Blueprint → loading stages cycle
6. Output panel shows Growth Check (collapsible), PRD, .env + Copy, Start Over

- [ ] **Step 3: Check console for errors**

Open browser devtools → Console. There should be zero React errors or HeroUI warnings.

- [ ] **Step 4: Final commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: migrate App.jsx to HeroUI Alert + Tailwind layout — complete HeroUI migration"
```
