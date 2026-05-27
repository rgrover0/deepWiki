# DeepWiki — Frontend Design Specification
> Source: Figma export (Project_Wiki_Website_Design v2)  
> Theme: Enterprise Blue (#003087) + Yellow (#ffc220)  
> Target: Angular 17+ with Tailwind CSS  
> Status: Reference for implementation — do not deviate from these specs

---

## 1. Design Tokens — Single Source of Truth

### Color Palette

```
PRIMARY PALETTE (light mode)
─────────────────────────────────────────────────────────
--background:          #ffffff       Page background
--foreground:          #1a2332       Body text
--primary:             #003087       Navy blue — buttons, icons, headers
--primary-foreground:  #ffffff       Text on primary
--accent:              #ffc220       Golden yellow — highlights, badges, active states
--accent-foreground:   #1a2332       Text on accent

SURFACE COLOURS
─────────────────────────────────────────────────────────
--card:                #ffffff       Card background
--card-foreground:     #1a2332       Card text
--secondary:           #f5f7fa       Subtle background fills
--secondary-foreground:#1a2332
--muted:               #e8ecf1       Disabled/muted background
--muted-foreground:    #5a6b7f       Muted/placeholder text
--border:              #d4dce6       Borders and dividers

SIDEBAR (left nav / header)
─────────────────────────────────────────────────────────
--sidebar:             #003087       Same as primary
--sidebar-foreground:  #ffffff
--sidebar-primary:     #ffc220       Active item accent
--sidebar-accent:      #004d99       Hover state
--sidebar-border:      #002359       Darker border

SEMANTIC
─────────────────────────────────────────────────────────
--destructive:         #d4183d       Delete / error red
--destructive-foreground: #ffffff

CHART COLOURS
─────────────────────────────────────────────────────────
--chart-1: #003087    chart-2: #ffc220
--chart-3: #0066cc    chart-4: #ffdb4d    chart-5: #004d99

BORDER RADIUS
─────────────────────────────────────────────────────────
--radius:    0.5rem   (8px)
--radius-sm: 0.25rem  (4px)
--radius-md: 0.375rem (6px)
--radius-lg: 0.5rem   (8px)
--radius-xl: 0.75rem  (12px)
```

### Dark Mode Tokens

```
--background:   #0a1119       --foreground:   #e8ecf1
--card:         #1a2332       --primary:      #0066cc
--secondary:    #1f2937       --muted:        #2a3544
--muted-foreground: #9ca3af  --border:       #2a3544
--accent:       #ffc220       (unchanged — brand colour)
--sidebar:      #1a2332       --sidebar-primary: #ffc220
```

### tailwind.config.js — Copy Exactly

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background:  'var(--background)',
        foreground:  'var(--foreground)',
        primary: {
          DEFAULT: 'var(--primary)',
          foreground: 'var(--primary-foreground)',
        },
        secondary: {
          DEFAULT: 'var(--secondary)',
          foreground: 'var(--secondary-foreground)',
        },
        accent: {
          DEFAULT: 'var(--accent)',
          foreground: 'var(--accent-foreground)',
        },
        muted: {
          DEFAULT: 'var(--muted)',
          foreground: 'var(--muted-foreground)',
        },
        destructive: {
          DEFAULT: 'var(--destructive)',
          foreground: 'var(--destructive-foreground)',
        },
        card: {
          DEFAULT: 'var(--card)',
          foreground: 'var(--card-foreground)',
        },
        border:    'var(--border)',
        input:     'var(--input)',
        ring:      'var(--ring)',
        sidebar: {
          DEFAULT:          'var(--sidebar)',
          foreground:       'var(--sidebar-foreground)',
          primary:          'var(--sidebar-primary)',
          'primary-foreground': 'var(--sidebar-primary-foreground)',
          accent:           'var(--sidebar-accent)',
          'accent-foreground':  'var(--sidebar-accent-foreground)',
          border:           'var(--sidebar-border)',
          ring:             'var(--sidebar-ring)',
        },
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
      },
    },
  },
};
```

### styles/theme.css — Import in styles.scss

```css
:root {
  --background:              #ffffff;
  --foreground:              #1a2332;
  --card:                    #ffffff;
  --card-foreground:         #1a2332;
  --popover:                 #ffffff;
  --popover-foreground:      #1a2332;
  --primary:                 #003087;
  --primary-foreground:      #ffffff;
  --secondary:               #f5f7fa;
  --secondary-foreground:    #1a2332;
  --muted:                   #e8ecf1;
  --muted-foreground:        #5a6b7f;
  --accent:                  #ffc220;
  --accent-foreground:       #1a2332;
  --destructive:             #d4183d;
  --destructive-foreground:  #ffffff;
  --border:                  #d4dce6;
  --input:                   transparent;
  --input-background:        #f5f7fa;
  --ring:                    #003087;
  --radius:                  0.5rem;
  --sidebar:                 #003087;
  --sidebar-foreground:      #ffffff;
  --sidebar-primary:         #ffc220;
  --sidebar-primary-foreground: #1a2332;
  --sidebar-accent:          #004d99;
  --sidebar-accent-foreground: #ffffff;
  --sidebar-border:          #002359;
  --sidebar-ring:            #ffc220;
}

.dark {
  --background:   #0a1119;    --foreground:   #e8ecf1;
  --card:         #1a2332;    --card-foreground: #e8ecf1;
  --primary:      #0066cc;    --primary-foreground: #ffffff;
  --secondary:    #1f2937;    --secondary-foreground: #e8ecf1;
  --muted:        #2a3544;    --muted-foreground: #9ca3af;
  --accent:       #ffc220;    --accent-foreground: #1a2332;
  --border:       #2a3544;    --sidebar: #1a2332;
  --sidebar-primary: #ffc220;
}
```

---

## 2. Typography

```
Font family: Inter (primary), system-ui fallback
Base size:   16px (var(--font-size))

h1 → text-4xl  font-bold   tracking-tight   (project titles)
h2 → text-2xl  font-semibold                (section headers)
h3 → text-lg   font-medium                  (card titles)
h4 → text-base font-medium
p  → text-base font-normal  leading-relaxed
small/labels → text-sm, text-xs
muted text → text-muted-foreground (var: #5a6b7f)
```

---

## 3. App Shell — Layout Component

### Header (sticky, always visible)

```
Background:  bg-primary              (#003087 blue)
Text colour: text-primary-foreground (#ffffff)
Height:      h-16 (64px)
Position:    sticky top-0 z-50 border-b

LOGO (left)
  Icon:   <Layers h-6 w-6 text-accent />     (yellow icon)
  Text:   "DeepWiki"  font-bold text-xl

NAV LINKS (ml-10, gap-6)
  Active:   text-accent (#ffc220)
  Inactive: text-primary-foreground/90
  Hover:    hover:text-accent
  Icons:    h-4 w-4 prefix each link

  / → <Layers />  "All Projects"
  /search → <Search />  "Search"
  /admin  → <Settings /> "Admin"

SEARCH BAR (ml-auto, w-64)
  <Search h-4 w-4 absolute left-2.5 top-2.5 text-muted-foreground />
  Input:  bg-primary-foreground/10
          border-primary-foreground/20
          text-primary-foreground
          placeholder:text-primary-foreground/60
  Placeholder: "Quick search..."
```

### Footer

```
border-t  bg-muted/30  py-8  mt-16
Left:  <Layers h-5 w-5 text-primary />  "DeepWiki - Technical Documentation Platform"
Right: "Powered by AI-assisted documentation"
Both:  text-sm text-muted-foreground
```

### Main Content Wrapper

```html
<main class="container py-8 px-4">
  <router-outlet />
</main>
```

---

## 4. Page: Projects Portfolio  `/`

### Page Header

```
h1: "Project Portfolio"           text-4xl font-bold tracking-tight
p:  "Explore our technology ecosystem across N projects in M application suites"
    text-muted-foreground text-lg
```

### Suite Tabs

```
<dw-tabs [value]="selectedSuite" class="w-full">
  <dw-tabs-list class="w-full justify-start">
    Tab: "All Projects (N)"
    Tab per suite: "Suite Name (count)"
  </dw-tabs-list>
```

### "All" Tab — Grouped by Suite

Each suite group:
```
SUITE HEADER:
  <div class="h-1 w-12 bg-accent rounded" />     ← yellow accent bar
  <h2 class="text-2xl font-semibold">Suite Name</h2>
  <dw-badge variant="secondary">N projects</dw-badge>

PROJECT GRID:
  class="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
```

### Project Card

```
<a routerLink="/project/:id">
  <dw-card class="h-full hover:shadow-lg transition-all hover:border-primary/50 group">
    HEADER:
      <Layers h-8 w-8 text-primary mb-2 />         ← blue Layers icon
      Docs badge (if has confluenceLink/repo)  →  <dw-badge variant="secondary">Docs</dw-badge>
      <ArrowRight h-5 w-5 text-muted-foreground group-hover:text-accent />  ← yellow on hover

      <CardTitle class="group-hover:text-primary">Project Name</CardTitle>
      <CardDescription>Short description</CardDescription>

    CONTENT:
      "Tech Stack" label → text-xs text-muted-foreground
      Tech badges → <dw-badge variant="outline" class="text-xs">tech</dw-badge>
      Show max 3, then "+N more" badge

      "Modules" label → text-xs text-muted-foreground
      Count → text-sm "N modules"
```

---

## 5. Page: Project Detail  `/project/:id`

### Back Button

```
<dw-button variant="ghost" class="mb-4">
  <ArrowLeft mr-2 h-4 w-4 /> Back to Projects
</dw-button>
```

### Project Header

```
ROW 1:
  h1: Project Name  text-4xl font-bold tracking-tight
  <dw-badge variant="secondary" class="bg-accent text-accent-foreground">Suite Name</dw-badge>
  ↑ Yellow badge with dark text

p: Description  text-lg text-muted-foreground

ROW 2 (tech stack):
  <dw-badge variant="outline">tech</dw-badge>  (all, not limited to 3)
```

### Stats Bar (3 cards, md:grid-cols-3)

```
CARD 1: Modules
  Icon:  <Package h-4 w-4 text-primary />
  Value: N  (text-2xl font-bold)
  Label: "Active modules"  (text-xs text-muted-foreground)

CARD 2: Relations
  Icon:  <Network h-4 w-4 text-primary />
  Value: N
  Label: "Connected services"

CARD 3: APIs
  Icon:  <GitBranch h-4 w-4 text-primary />
  Value: N
  Label: "Total endpoints"
```

### Project Story + Documentation (md:grid-cols-2)

```
LEFT — Project Story & History
  Icon: <Clock h-5 w-5 text-primary />
  CardTitle: "Project Story & History"
  Body: project.story  text-muted-foreground leading-relaxed

RIGHT — Documentation & Resources
  Icon: <Link2 h-5 w-5 text-primary />
  CardTitle: "Documentation & Resources"

  Repository link (if exists):
    Icon: <GitBranch h-4 w-4 text-muted-foreground />
    Title: "Repository"
    Sub:   "View source code"
    Right: <ExternalLink group-hover:text-primary />
    Container: border rounded-lg hover:bg-accent/5

  Confluence link (if exists):
    Icon: <FileText h-4 w-4 text-muted-foreground />
    Title: "Confluence Documentation"
    Sub:   "Full documentation"

  Empty state: "No external documentation links available"
               text-sm text-muted-foreground text-center py-4
```

### Architecture Diagram (optional)

```
Only renders if project.architectureDiagram is set.

CardHeader:
  Icon: <Image h-5 w-5 text-primary />
  Title: "Architecture Diagram"
  Desc:  "Visual representation of the system architecture"

CardContent:
  <div class="border rounded-lg overflow-hidden">
    <img [src]="project.architectureDiagram" class="w-full h-auto" />
  </div>
```

### Modules & Features Section

```
h2: <Package h-6 w-6 text-primary />  "Modules & Features"
    text-2xl font-semibold

Grid: grid gap-4 md:grid-cols-2

MODULE CARD:
  CardTitle: module.name
  CardDescription: module.description
  CardContent:
    "Key Features:" text-sm font-medium
    ul: each feature →
      <div class="h-1.5 w-1.5 rounded-full bg-accent" />  ← yellow dot
      feature text  text-sm text-muted-foreground
```

### Project Relations Section

```
h2: <Network h-6 w-6 text-primary />  "Project Relations"
    text-2xl font-semibold

RELATION CARD (per relation):
  TYPE BADGE (colour coded):
    depends-on:       bg-blue-100 text-blue-700
    provides-to:      bg-green-100 text-green-700
    integrates-with:  bg-purple-100 text-purple-700

  projectName:   font-medium
  description:   text-sm text-muted-foreground
  Link button:   <ExternalLink h-4 w-4 />  → /project/:projectId
```

### AI Intelligence Tabs (bottom of page)

```
<dw-separator class="my-8" />

<dw-tabs defaultValue="ask" class="w-full">
  <dw-tabs-list class="grid w-full grid-cols-4">
    "ask"        <MessageSquare h-4 w-4 />  "Ask DeepWiki"
    "plan"       <FlaskConical h-4 w-4 />   "Plan & Tests"
    "comparison" <BarChart3 h-4 w-4 />      "Live Comparison"
    "api"        <GitBranch h-4 w-4 />      "API Catalog"
  </dw-tabs-list>
```

---

## 6. Tab Sections — Project Detail

### 6A. Ask DeepWiki Tab

```
CARD:
  Icon: <MessageSquare h-5 w-5 text-primary />
  Title: "Ask about {project.name}"
  Desc:  "Get instant answers about modules, features, architecture, and implementation details"

EMPTY STATE (no messages yet):
  "Try asking:"  text-sm text-muted-foreground

  4 SUGGESTED QUESTIONS (grid gap-2):
    <dw-button variant="outline" class="justify-start text-left h-auto py-3">
      <Sparkles h-4 w-4 mr-2 flex-shrink-0 text-accent />    ← yellow sparkles
      Question text  text-sm

CHAT MESSAGES (max-h-96 overflow-y-auto):
  User message  → justify-end
    bg-primary text-primary-foreground  rounded-lg px-4 py-2 max-w-[80%]

  Assistant message → justify-start
    bg-muted text-foreground  rounded-lg px-4 py-2 max-w-[80%]

  Loading:
    bg-muted  rounded-lg px-4 py-2
    3 dots animation  (●●●  animate-pulse)

INPUT ROW (below messages):
  <dw-textarea placeholder="Ask anything about {project.name}..." />
  <dw-button [disabled]="loading">
    <Send h-4 w-4 />
```

### 6B. Plan & Tests Tab

```
CARD:
  Icon: <FlaskConical h-5 w-5 text-primary />
  Title: "Feature Planning & Test Generation"
  Desc:  "Describe a new feature and get an implementation plan with comprehensive test cases"

EMPTY STATE:
  "Example features:" text-sm text-muted-foreground
  CHIPS (flex flex-wrap gap-2):
    <dw-button variant="outline" size="sm">
      <Sparkles h-3 w-3 mr-2 text-accent />    ← yellow
      Example feature text

  <dw-textarea placeholder="Describe the feature you want to add..." class="min-h-[100px]" />
  <dw-button>
    <Sparkles h-4 w-4 />  Generate Plan & Tests

RESULT STATE (after generation):
  Tabs: "Implementation Plan" | "Test Cases"

  IMPLEMENTATION PLAN TAB:
    Card with pre-formatted text
    Feature name as h3
    Implementation steps as prose

  TEST CASES TAB:
    Card list, each test case:
      <CheckCircle2 h-5 w-5 text-primary />
      Test description  font-medium
      <Code h-4 w-4 />  code snippet block

  <dw-button variant="outline" (click)="reset()">
    Start Over
```

### 6C. Live Comparison Tab

```
HIGHLIGHT CARD (border-accent/50 bg-gradient-to-br from-accent/5 to-primary/5):
  Icon: <BarChart3 h-5 w-5 text-primary />
  Title: "Performance & Cost Optimization"
  Desc:  "Real-time comparison of token usage and cost savings"

  SUMMARY GRID (md:grid-cols-2):
    LEFT — Token Savings:
      <Zap h-4 w-4 />  "Token Savings"  text-muted-foreground text-sm
      "66%"  text-3xl font-bold text-primary
      "2500 → 850 tokens"  text-xs text-muted-foreground

    RIGHT — Cost Savings:
      <DollarSign h-4 w-4 />  "Cost Savings"  text-muted-foreground text-sm
      "$2050/mo"  text-3xl font-bold text-accent    ← yellow value
      "64% reduction"  text-xs text-muted-foreground

METRICS LIST (4 metric cards):
  Each card:
    Metric name  font-semibold
    Improvement badge  → "60% improvement"  text-green-600 bg-green-50
    Before value  →  text-sm text-muted-foreground  "Before: 450ms"
    After value   →  text-sm font-medium             "After: 180ms"
    <dw-progress [value]="metric.improvement" />    ← progress bar
```

**Metric data:**
```
API Response Time:       450ms → 180ms  (60% improvement)
Token Usage per Request: 2500  → 850    (66% improvement)
Monthly API Cost:        $3200 → $1150  (64% improvement)
Cache Hit Rate:          45%   → 87%    (93% improvement)
```

### 6D. API Catalog Tab

```
CARD:
  Icon: <GitBranch h-5 w-5 text-primary />
  Title: "API Catalog — {project.name}"
  Desc:  "Complete API registry showing exposed and consumed endpoints"

SEARCH INPUT:
  <Search h-4 w-4 absolute />
  placeholder="Search APIs by name, endpoint, or description..."

TABS: "Exposed APIs (N)" | "Consumed APIs (N)"

API CARD (per endpoint):
  ROW 1:
    METHOD BADGE (colour coded):
      GET    → bg-blue-100   text-blue-700
      POST   → bg-green-100  text-green-700
      PUT    → bg-yellow-100 text-yellow-700
      DELETE → bg-red-100    text-red-700
      PATCH  → bg-purple-100 text-purple-700

    Name:  font-semibold
    <dw-button variant="outline" size="sm">
      <Code h-4 w-4 />  View Docs

  ROW 2:
    <code class="text-sm bg-muted px-2 py-1 rounded">endpoint path</code>

  ROW 3:
    description  text-sm text-muted-foreground

  ROW 4 (type indicator):
    Exposed: <ArrowUpFromLine h-3 w-3 />  "Exposed API"
    Consumed: <ArrowDownToLine h-3 w-3 />  "Consumed API"
    Both: <dw-badge variant="outline" class="text-xs">
```

---

## 7. Page: Search  `/search`

### Page Header

```
h1: "Search Projects"          text-4xl font-bold tracking-tight
p:  "Search across all projects, modules, and technologies"
    text-muted-foreground text-lg
```

### Search Input

```
<div class="relative">
  <Search class="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
  <dw-input
    placeholder="Search by project name, description, module, or technology..."
    class="pl-10 h-12 text-lg"
  />
</div>
```

### Tech Filter Card

```
CardHeader:
  <Filter h-5 w-5 text-primary />  "Filter by Technology"
  "Clear all" button (ghost, sm) — shows when filters active

CardContent:
  All unique tech values as toggle badges
  Inactive: <dw-badge variant="outline" class="cursor-pointer hover:bg-primary/90">
  Active:   <dw-badge variant="default">  (blue filled)
```

### Results

```
Header: "N results" text-xl font-semibold
        "Reset filters" button (outline, sm) — shows when active

EMPTY STATE:
  <Search h-12 w-12 text-muted-foreground mx-auto mb-4 />
  "No projects found"  text-lg font-semibold
  "Try adjusting your search query or filters"  text-muted-foreground

RESULT CARDS (full-width list):
  hover:shadow-lg hover:border-primary/50 group

  LEFT: h-12 w-12 rounded-lg bg-primary/10
        <Layers h-6 w-6 text-primary />

  CONTENT:
    Name: font-semibold text-lg group-hover:text-primary
    Suite badge: <dw-badge variant="secondary">
    Docs badge (if confluenceLink): <dw-badge variant="outline"><FileText h-3 w-3 />Docs</dw-badge>
    Repo badge (if repositoryUrl):  <dw-badge variant="outline"><GitBranch h-3 w-3 />Repo</dw-badge>
    Description: text-muted-foreground

    Tech badges: all of them
    Active filter tech: highlight with bg-primary/10 border-primary

    Stats: "N modules · N integrations · N APIs"  text-sm text-muted-foreground

  RIGHT: <ArrowRight h-5 w-5 text-muted-foreground group-hover:text-accent />
```

---

## 8. Page: Admin  `/admin`

### Page Header

```
<Settings h-8 w-8 text-primary />
h1: "Admin Panel"   text-4xl font-bold tracking-tight
p:  "Manage projects, suites, and documentation links"
    text-muted-foreground text-lg
```

### Admin Tabs

```
grid-cols-2 tabs:
  "add-project"  <Plus />     "Add Project"
  "manage"       <Settings /> "Manage Projects"
```

### Add Project Tab

**Form fields:**

```
PROJECT NAME *
  <dw-label>Project Name</dw-label>
  <dw-input placeholder="e.g. Authentication Service" />

SUITE *
  Mode toggle:
    [Existing Suite] dropdown  ←→  [Create New Suite] text input
    <dw-button variant="outline" size="sm">Create New Suite / Use Existing Suite</dw-button>

  Existing: <Select> with existing suite options
  New:      <dw-input placeholder="e.g. Core Platform" />

TECH STACK
  Input + "Add" button (inline)
  Chips (added items): tech name + <X> remove button
  <dw-badge variant="secondary" class="cursor-pointer">tech <X /></dw-badge>

DESCRIPTION *
  <dw-textarea placeholder="Brief description..." rows=3 />

PROJECT STORY
  <dw-textarea placeholder="History and context..." rows=4 />

─── DOCUMENTATION SECTION ──────────────────────────────────────
REPOSITORY URL
  <GitBranch h-4 w-4 text-muted-foreground />
  <dw-input placeholder="https://github.com/org/repo" />

CONFLUENCE LINK
  <FileText h-4 w-4 text-muted-foreground />
  <dw-input placeholder="https://confluence.company.com/..." />

ARCHITECTURE DIAGRAM
  File upload or URL input toggle

  File upload:
    <label class="border-2 border-dashed border-border rounded-lg p-8 cursor-pointer hover:border-primary/50">
      <Upload h-8 w-8 text-muted-foreground mx-auto mb-2 />
      "Click to upload or drag and drop"  text-sm text-muted-foreground
      "PNG, JPG, SVG (max 10MB)"          text-xs text-muted-foreground
    </label>

    After upload: show image preview with filename

  URL input:
    <dw-input placeholder="https://..." />

─── SUBMIT ────────────────────────────────────────────────────
<dw-button class="w-full" size="lg">
  <Save h-4 w-4 />  Add Project
```

### Manage Projects Tab

```
SEARCH: <dw-input placeholder="Filter projects..." />

PROJECT LIST (per project):
  Name: font-semibold
  Suite badge: <dw-badge variant="secondary">
  Tech badges (first 3): <dw-badge variant="outline" class="text-xs">

  ACTIONS:
    Edit: <dw-button variant="outline" size="sm"><Settings h-4 w-4 /></dw-button>
    Delete: confirm dialog before delete
      DialogTitle: "Delete {name}?"
      DialogDesc:  "This action cannot be undone..."
      Cancel + <dw-button variant="destructive">Delete</dw-button>
```

### Admin Guide Tab (optional)

```
Tab: "guide"  <Book /> "Getting Started"

Sections:
1. Adding Your First Project
2. Setting Up Suites
3. Linking Documentation
4. Managing Architecture Diagrams

Each section as accordion-style card with numbered steps.
```

---

## 9. Data Interfaces — TypeScript

```typescript
// core/models/project.model.ts

export interface Module {
  id: string;
  name: string;
  description: string;
  features: string[];
}

export interface Relation {
  projectId:   string;
  projectName: string;
  type:        'depends-on' | 'provides-to' | 'integrates-with';
  description: string;
}

export interface API {
  id:          string;
  name:        string;
  type:        'exposed' | 'consumed';
  method:      'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  endpoint:    string;
  description: string;
}

export interface Project {
  id:                  string;
  name:                string;
  suite:               string;
  techStack:           string[];
  description:         string;
  story:               string;
  modules:             Module[];
  relations:           Relation[];
  apis:                API[];
  confluenceLink?:     string;   // optional
  architectureDiagram?: string;  // optional — URL or base64
  repositoryUrl?:      string;   // optional
}

export interface Suite {
  id:          string;
  name:        string;
  description: string;
  projectIds:  string[];
}
```

---

## 10. Shared Angular Components — Specs

### BadgeComponent

```
selector: dw-badge
input: variant: 'default' | 'secondary' | 'outline' | 'destructive' = 'default'

CSS classes:
  base:        inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold
  default:     bg-primary text-primary-foreground               ← blue + white
  secondary:   bg-secondary text-secondary-foreground            ← light grey
  outline:     border border-border text-foreground bg-transparent
  destructive: bg-destructive text-destructive-foreground        ← red + white
```

### ButtonComponent

```
selector: dw-button
inputs: variant, size, disabled, asChild

CSS:
  base:        inline-flex items-center justify-center gap-2 rounded-md text-sm
               font-medium transition-all disabled:opacity-50
  default:     bg-primary text-primary-foreground hover:bg-primary/90
  destructive: bg-destructive text-white hover:bg-destructive/90
  outline:     border bg-background text-foreground hover:bg-accent hover:text-accent-foreground
  secondary:   bg-secondary text-secondary-foreground hover:bg-secondary/80
  ghost:       hover:bg-accent hover:text-accent-foreground
  link:        text-primary underline-offset-4 hover:underline

Sizes:
  default: h-9 px-4 py-2
  sm:      h-8 px-3 gap-1.5
  lg:      h-10 px-6
  icon:    size-9
```

### CardComponent

```
selector: dw-card
template:
  <div class="bg-card text-card-foreground flex flex-col gap-6 rounded-xl border [class]">
    <ng-content />
  </div>

Sub-components:
  dw-card-header  → px-6 pt-6
  dw-card-title   → font-semibold leading-none (h4)
  dw-card-desc    → text-muted-foreground (p)
  dw-card-content → px-6 pb-6
```

### TabsComponent

```
selector: dw-tabs
inputs:  value (selected tab)
outputs: valueChange

dw-tabs-list:
  bg-muted text-muted-foreground  rounded-lg p-1
  inline-flex h-9 items-center

dw-tabs-trigger:
  Inactive: text-muted-foreground
  Active:   bg-background text-foreground shadow-sm  rounded-md
  Includes icons as ng-content before text

dw-tabs-content:
  Hidden when not active
  Animated: fade in
```

### ProgressComponent

```
selector: dw-progress
input: value (0-100)

<div class="relative h-2 w-full overflow-hidden rounded-full bg-secondary">
  <div class="h-full bg-primary transition-all" [style.width.%]="value"></div>
</div>
```

### MethodColorPipe

```typescript
@Pipe({ name: 'methodColor', standalone: true })
export class MethodColorPipe implements PipeTransform {
  transform(method: string): string {
    const map: Record<string, string> = {
      GET:    'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
      POST:   'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
      PUT:    'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
      DELETE: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
      PATCH:  'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    };
    return map[method?.toUpperCase()] ?? 'bg-gray-100 text-gray-700';
  }
}
```

### RelationColorPipe

```typescript
@Pipe({ name: 'relationColor', standalone: true })
export class RelationColorPipe implements PipeTransform {
  transform(type: string): string {
    const map: Record<string, string> = {
      'depends-on':      'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
      'provides-to':     'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
      'integrates-with': 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    };
    return map[type] ?? 'bg-gray-100 text-gray-700';
  }
}
```

---

## 11. Routing

```typescript
// app.routes.ts
export const routes: Routes = [
  {
    path: '',
    component: AppShellComponent,
    children: [
      {
        path: '',
        loadComponent: () => import('./features/projects/projects.component')
          .then(m => m.ProjectsComponent)
      },
      {
        path: 'project/:id',
        loadComponent: () => import('./features/project-detail/project-detail.component')
          .then(m => m.ProjectDetailComponent)
      },
      {
        path: 'search',
        loadComponent: () => import('./features/search/search.component')
          .then(m => m.SearchComponent)
      },
      {
        path: 'admin',
        loadComponent: () => import('./features/admin/admin.component')
          .then(m => m.AdminComponent)
      },
    ]
  },
  {
    // Graph visualization — full screen, no shell
    path: 'graph',
    loadComponent: () => import('./features/graph/graph.component')
      .then(m => m.GraphComponent)
  },
  { path: '**', redirectTo: '' }
];
```

---

## 12. Icons Reference — Lucide Angular

```
Install: npm install lucide-angular

Icons used (import these):
  Layers         → Logo, all-projects nav, project cards
  Search         → Search nav, search page, API search
  Settings       → Admin nav, admin page header
  ArrowRight     → Card hover indicator
  ArrowLeft      → Back button
  Package        → Modules section header
  Network        → Relations section header
  GitBranch      → APIs stat card + API Catalog tab
  Clock          → Project Story card
  Link2          → Documentation card
  ExternalLink   → External links
  FileText       → Confluence link
  Image          → Architecture diagram card
  MessageSquare  → Ask DeepWiki tab
  FlaskConical   → Plan & Tests tab
  BarChart3      → Live Comparison tab
  Sparkles       → Suggested questions, example features
  Send           → Chat submit
  Filter         → Tech filter
  ArrowUpFromLine   → Exposed API indicator
  ArrowDownToLine   → Consumed API indicator
  Code           → View Docs button
  CheckCircle2   → Test case item
  TrendingDown   → Cost savings
  Zap            → Token savings
  DollarSign     → Cost metric
  Plus           → Add project tab
  Upload         → File upload
  Save           → Submit form
  Trash2         → Delete project
```

---

## 13. Interaction States

### Card Hover (project cards, search results)

```
Normal:  border-border  shadow-none
Hover:   border-primary/50  shadow-lg
Group hover triggers:
  - ArrowRight: text-muted-foreground → text-accent   (yellow)
  - CardTitle:  text-foreground → text-primary        (blue)
```

### Button Active/Focus

```
Focus:  ring-2 ring-ring/50 (ring: --ring: #003087)
Active: scale-95 transition
```

### Tab Active

```
Active tab:  bg-background text-foreground shadow-sm
Inactive:    text-muted-foreground hover:text-foreground
```

### Badge Toggle (tech filter)

```
Inactive: variant="outline"  cursor-pointer hover:bg-primary/90
Active:   variant="default"  (blue fill)
```

---

## 14. Empty States

### No Messages (Ask DeepWiki)

```
Show suggested questions grid immediately.
Each: outline button with Sparkles icon (text-accent).
```

### No Search Results

```
<Search h-12 w-12 text-muted-foreground mx-auto mb-4 />
"No projects found"  text-lg font-semibold mb-2
"Try adjusting your search query or filters"  text-muted-foreground
```

### No Documentation Links

```
"No external documentation links available"
text-sm text-muted-foreground text-center py-4
```

---

## 15. Responsive Breakpoints

```
Mobile  (default):  single column
Tablet  (md: 768px): 2 columns for project cards, stats, story+docs
Desktop (lg: 1024px): 3 columns for project cards
Container: max-w-7xl mx-auto px-4
```

---

## 16. Animation/Transition

```
All transitions: transition-all  (or transition-colors for colour only)
Duration: default (150ms)
Card shadows: shadow-none → shadow-lg on hover
Arrow icons: use group-hover for parent-triggered child transitions

Loading state (Ask DeepWiki):
  3 dots: bg-muted rounded-full  animate-pulse
  Pattern: ●●●  with staggered animation
```

---

## 17. Known Design Rules

```
⚠️  ACCENT (#ffc220) is YELLOW — used for:
    - Active nav link text
    - Logo icon
    - Suite section bar (h-1 w-12 bg-accent)
    - Feature dot bullets (h-1.5 w-1.5 rounded-full bg-accent)
    - Sparkles icon on suggested questions
    - Arrow icon on card hover (group-hover:text-accent)
    - Cost savings value (text-accent in comparison)
    - Suite badge on project detail (bg-accent text-accent-foreground)
    - Sidebar active item

⚠️  PRIMARY (#003087) is NAVY BLUE — used for:
    - Header background
    - All "primary" buttons
    - All icon colours (text-primary)
    - Section heading icons
    - Stat card values (text-primary)
    - Token savings value (text-primary)
    - Focus rings

⚠️  NEVER use generic blue-500 or yellow-400 — always use CSS var tokens

⚠️  Card rounded: rounded-xl (not rounded-lg) — the Card component default
⚠️  Separator before AI tabs: <dw-separator class="my-8" />
⚠️  AI tabs grid: grid-cols-4 (not justify-start)  [detail page only]
⚠️  Suite tabs:   justify-start w-full               [projects page]
```

---

*Last updated: May 2026 from Figma export v2 (blue/yellow enterprise theme).*  
*Do not modify design tokens without updating this file.*  
*All hex values are final — do not substitute with Tailwind default colours.*
