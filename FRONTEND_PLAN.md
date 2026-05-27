# DeepWiki — Angular Frontend Plan
> Phase 2 Pre-work · Senior Engineering Plan  
> Source: DeepWiki.jsx (D3 graph) + Project_Wiki_Website_Design (Figma)  
> Output: Angular 17+ app replacing Streamlit UI

---

## 1. What We Have → What We Build

### Source Analysis

| Source | What It Has | What We Keep |
|---|---|---|
| `DeepWiki.jsx` | D3 force graph, dark space theme, 3-level Universe→Suite→Project drill-down, JARVIS visual polish, suite/project/module data structure | **All of it** — ported to Angular feature module |
| Figma design | Card-based portfolio, project detail tabs, Ask DeepWiki chat, API catalog, Live Comparison, Search | **All of it** — Angular components with Tailwind |
| Streamlit portal | 6 pages, FastAPI integration, token comparison | **Backend API contracts only** — UI replaced |

### The Merge Strategy

```
/graph          →  Dark D3 visualization (JSX ported to Angular)
/               →  Projects portfolio (Figma card design)
/project/:id    →  Project detail with 5 tabs (Figma sections)
/search         →  Search + tech filter (Figma search page)
```

Two visual modes, one app. The graph is a power-user "architecture view". Cards are the everyday "documentation view". Both are first-class routes.

---

## 2. Project Setup

### Stack

```
Angular CLI 17+       ng new deepwiki-ui --standalone --routing --style=scss
Tailwind CSS 3.x      npm install tailwindcss postcss autoprefixer
D3 v7                 npm install d3 @types/d3
Lucide Angular        npm install lucide-angular
RxJS 7 (bundled)
HttpClient (Angular)
```

### tailwind.config.js — Figma Design Tokens

```javascript
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: {
        // Figma light theme tokens
        background:  '#ffffff',
        foreground:  '#030213',
        primary:     '#030213',
        'primary-foreground': '#ffffff',
        secondary:   '#f3f3f5',
        muted:       '#ececf0',
        'muted-foreground': '#717182',
        accent:      '#e9ebef',
        border:      'rgba(0,0,0,0.1)',
        destructive: '#d4183d',

        // D3 graph dark theme tokens (graph route only)
        'graph-bg':       '#020C18',
        'graph-panel':    '#030E1C',
        'graph-border':   '#0D3464',
        'graph-border-hi':'#1A6CC0',
        'graph-text':     '#507898',
        'graph-text-hi':  '#B0D4EE',
        'graph-yellow':   '#FFD100',
        'graph-blue':     '#2878CC',
        'graph-teal':     '#1D9E75',
        'graph-purple':   '#8870DD',
      },
      fontFamily: {
        sans:  ['Inter', 'system-ui', 'sans-serif'],
        mono:  ['"Courier New"', 'monospace'],   // graph only
      },
      borderRadius: { DEFAULT: '0.625rem' },
    }
  }
};
```

### Environment Files

```typescript
// environments/environment.ts (dev)
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
};

// environments/environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'https://your-app.railway.app',
};
```

---

## 3. Directory Structure

```
deepwiki-ui/
├── src/
│   ├── app/
│   │   ├── core/
│   │   │   ├── models/
│   │   │   │   ├── project.model.ts     ← Project, Module, Relation, API interfaces
│   │   │   │   ├── suite.model.ts       ← Suite, ApplicationSuite
│   │   │   │   ├── graph.model.ts       ← GraphNode, GraphLink (D3 types)
│   │   │   │   ├── wiki.model.ts        ← AskRequest, AskResponse, SearchResult
│   │   │   │   └── index.ts             ← barrel export
│   │   │   └── services/
│   │   │       ├── project.service.ts   ← CRUD for projects/suites (FastAPI)
│   │   │       ├── wiki.service.ts      ← ask(), search(), flow()
│   │   │       ├── graph-data.service.ts ← buildCosmosGraph/buildSuiteGraph/buildProjectGraph
│   │   │       └── d3-renderer.service.ts ← D3 simulation logic (outside Angular)
│   │   │
│   │   ├── shared/
│   │   │   ├── components/
│   │   │   │   ├── badge/
│   │   │   │   │   └── badge.component.ts   ← variant: default|secondary|outline|destructive
│   │   │   │   ├── card/
│   │   │   │   │   └── card.component.ts    ← CardHeader, CardContent, CardTitle, CardDesc
│   │   │   │   ├── button/
│   │   │   │   │   └── button.component.ts  ← variant: default|outline|ghost|link
│   │   │   │   ├── input/
│   │   │   │   │   └── input.component.ts
│   │   │   │   ├── tabs/
│   │   │   │   │   └── tabs.component.ts    ← TabsList, TabsTrigger, TabsContent
│   │   │   │   ├── dialog/
│   │   │   │   │   └── dialog.component.ts
│   │   │   │   ├── progress/
│   │   │   │   │   └── progress.component.ts
│   │   │   │   └── textarea/
│   │   │   │       └── textarea.component.ts
│   │   │   └── pipes/
│   │   │       ├── method-color.pipe.ts    ← GET→blue, POST→green, DELETE→red
│   │   │       └── truncate.pipe.ts
│   │   │
│   │   ├── layout/
│   │   │   ├── header/
│   │   │   │   ├── header.component.ts
│   │   │   │   └── header.component.html
│   │   │   ├── footer/
│   │   │   │   └── footer.component.ts
│   │   │   └── app-shell.component.ts   ← wraps header + router-outlet + footer
│   │   │
│   │   ├── features/
│   │   │   │
│   │   │   ├── projects/                    ← LAZY LOADED
│   │   │   │   ├── components/
│   │   │   │   │   ├── project-card/
│   │   │   │   │   │   ├── project-card.component.ts
│   │   │   │   │   │   └── project-card.component.html
│   │   │   │   │   └── suite-group/
│   │   │   │   │       └── suite-group.component.ts
│   │   │   │   ├── projects.component.ts
│   │   │   │   ├── projects.component.html
│   │   │   │   └── projects.routes.ts
│   │   │   │
│   │   │   ├── project-detail/              ← LAZY LOADED
│   │   │   │   ├── sections/
│   │   │   │   │   ├── modules-section/
│   │   │   │   │   │   └── modules-section.component.ts
│   │   │   │   │   ├── api-catalog-section/
│   │   │   │   │   │   ├── api-catalog-section.component.ts
│   │   │   │   │   │   └── api-card/api-card.component.ts
│   │   │   │   │   ├── ask-deepwiki-section/
│   │   │   │   │   │   └── ask-deepwiki-section.component.ts  ← chat UI + HTTP
│   │   │   │   │   ├── plan-tests-section/
│   │   │   │   │   │   └── plan-tests-section.component.ts
│   │   │   │   │   └── live-comparison-section/
│   │   │   │   │       └── live-comparison-section.component.ts
│   │   │   │   ├── project-detail.component.ts
│   │   │   │   ├── project-detail.component.html
│   │   │   │   └── project-detail.routes.ts
│   │   │   │
│   │   │   ├── search/                      ← LAZY LOADED
│   │   │   │   ├── search.component.ts
│   │   │   │   ├── search.component.html
│   │   │   │   └── search.routes.ts
│   │   │   │
│   │   │   └── graph/                       ← LAZY LOADED — dark theme
│   │   │       ├── components/
│   │   │       │   ├── force-graph/
│   │   │       │   │   ├── force-graph.component.ts   ← ViewChild for D3 container
│   │   │       │   │   └── force-graph.component.scss ← dark styles only
│   │   │       │   ├── info-panel/
│   │   │       │   │   └── info-panel.component.ts
│   │   │       │   ├── legend/
│   │   │       │   │   └── legend.component.ts
│   │   │       │   └── scan-bar/
│   │   │       │       └── scan-bar.component.ts
│   │   │       ├── graph.component.ts       ← host: dark theme class
│   │   │       ├── graph.component.scss
│   │   │       └── graph.routes.ts
│   │   │
│   │   ├── app.component.ts
│   │   ├── app.routes.ts
│   │   └── app.config.ts
│   │
│   ├── assets/
│   ├── environments/
│   └── styles/
│       ├── _variables.scss   ← Figma tokens as SCSS vars
│       ├── _graph.scss       ← D3 dark theme (scoped to .graph-mode)
│       └── styles.scss       ← Tailwind imports + global reset
```

---

## 4. Core Models

```typescript
// core/models/project.model.ts
export interface Module {
  id: string;
  name: string;
  description: string;
  features: string[];
  classCount?: number;
  type?: 'core' | 'security' | 'feature' | 'event' | 'analytics' | 'admin';
}

export interface Relation {
  projectId: string;
  projectName: string;
  type: 'depends-on' | 'provides-to' | 'integrates-with';
  description: string;
}

export interface ApiContract {
  id: string;
  name: string;
  type: 'exposed' | 'consumed';
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  endpoint: string;
  description: string;
  authRequired?: boolean;
}

export interface Project {
  id: string;
  name: string;
  suite: string;
  techStack: string[];
  description: string;
  story?: string;
  modules: Module[];
  relations: Relation[];
  apis: ApiContract[];
  status?: 'active' | 'beta' | 'deprecated';
  lastDeploy?: string;
}

// core/models/suite.model.ts
export interface Suite {
  id: string;
  name: string;
  description: string;
  color: string;
  projects: Project[];
}

// core/models/wiki.model.ts
export interface AskRequest {
  question: string;
  repo_id?: string;
  suite_id?: string;
  top_k?: number;
}

export interface AskResponse {
  answer: string;
  sources: string[];
  scores: number[];
}

export interface SearchResult {
  name: string;
  component_type: string;
  wiki_summary: string;
  score: number;
  repo_id?: string;
}

// core/models/graph.model.ts
export interface GraphNode {
  id: string;
  label: string;
  shortLabel: string;
  type: 'suite' | 'suite-center' | 'project' | 'project-center' | 'module' | 'external';
  color: string;
  r: number;
  data: Suite | Project | Module;
  alpha?: number;
  x?: number; y?: number; fx?: number; fy?: number;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  type: 'owns' | 'connects' | 'inter-suite';
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export type GraphLevel = 'cosmos' | 'suite' | 'project';
```

---

## 5. Core Services

### project.service.ts — Talks to FastAPI backend

```typescript
@Injectable({ providedIn: 'root' })
export class ProjectService {
  private http   = inject(HttpClient);
  private apiUrl = inject(ENVIRONMENT).apiUrl;

  // Connect to FastAPI /classes endpoint for now
  // Future: /suites endpoint returning full Suite structure
  getClasses(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/classes`);
  }

  getStats(): Observable<any> {
    return this.http.get(`${this.apiUrl}/stats`);
  }

  // Suites data — starts as local mock matching JSX structure,
  // replaced by API call when backend exposes /suites endpoint
  getSuites(): Observable<Suite[]> {
    return of(MOCK_SUITES);  // Phase 2: replace with http.get('/suites')
  }
}
```

### wiki.service.ts — LLM-backed features

```typescript
@Injectable({ providedIn: 'root' })
export class WikiService {
  private http   = inject(HttpClient);
  private apiUrl = inject(ENVIRONMENT).apiUrl;

  ask(req: AskRequest): Observable<AskResponse> {
    return this.http.post<AskResponse>(`${this.apiUrl}/ask`, req);
  }

  search(query: string, topK = 5): Observable<SearchResult[]> {
    return this.http.post<SearchResult[]>(`${this.apiUrl}/search`, { query, top_k: topK });
  }

  getFlow(entryPoint: string, repoId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/flow`, { entry_point: entryPoint, repo_id: repoId });
  }

  generatePlan(requirement: string, repoId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/plan`, { requirement, repo_id: repoId });
  }

  compare(query: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/compare`, { query, top_k: 5 });
  }
}
```

### graph-data.service.ts — Ported from JSX (pure logic, no DOM)

```typescript
@Injectable({ providedIn: 'root' })
export class GraphDataService {
  private projectService = inject(ProjectService);

  buildCosmosGraph(suites: Suite[], W: number, H: number): GraphData {
    // Port of buildCosmosGraph() from JSX
    // Positions suites in a circle, adds inter-suite links
  }

  buildSuiteGraph(suiteId: string, suites: Suite[], W: number, H: number): GraphData {
    // Port of buildSuiteGraph() from JSX
  }

  buildProjectGraph(projectId: string, suites: Suite[], W: number, H: number): GraphData {
    // Port of buildProjectGraph() from JSX
  }
}
```

### d3-renderer.service.ts — D3 simulation (runs outside NgZone)

```typescript
@Injectable({ providedIn: 'root' })
export class D3RendererService {
  private ngZone = inject(NgZone);

  render(
    svgElement: SVGSVGElement,
    graphData: GraphData,
    W: number, H: number,
    onNodeClick: (node: GraphNode) => void
  ): d3.Simulation<GraphNode, GraphLink> {
    // Runs entirely outside Angular zone — no change detection overhead
    return this.ngZone.runOutsideAngular(() => {
      const svg = d3.select(svgElement);
      svg.selectAll('*').remove();
      // ... all D3 logic ported from JSX ForceGraph component
      // ... glow filters, hex dot pattern, force simulation
      // ... node render (circles, ticks, labels)
      // ... link render (animated dash lines)
      // ... click handlers call ngZone.run(() => onNodeClick(node))
    });
  }

  destroy(simulation: d3.Simulation<any, any>): void {
    simulation?.stop();
  }
}
```

---

## 6. Shared Components — Matching Figma Design

### Badge Component

```typescript
@Component({
  selector: 'dw-badge',
  standalone: true,
  template: `
    <span [class]="classes()">
      <ng-content />
    </span>
  `
})
export class BadgeComponent {
  variant = input<'default'|'secondary'|'outline'|'destructive'>('default');
  classes = computed(() => {
    const base = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors';
    const variants = {
      default:     'bg-primary text-primary-foreground',
      secondary:   'bg-secondary text-secondary-foreground',
      outline:     'border border-border text-foreground',
      destructive: 'bg-destructive text-destructive-foreground',
    };
    return `${base} ${variants[this.variant()]}`;
  });
}
```

### Method Color Pipe

```typescript
@Pipe({ name: 'methodColor', standalone: true })
export class MethodColorPipe implements PipeTransform {
  transform(method: string): string {
    const map: Record<string, string> = {
      'GET':    'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
      'POST':   'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
      'PUT':    'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
      'DELETE': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
      'PATCH':  'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    };
    return map[method.toUpperCase()] ?? 'bg-gray-100 text-gray-700';
  }
}
```

---

## 7. Feature Implementation

### 7A — projects/ (Figma card design)

**Template structure:**
```html
<!-- projects.component.html -->
<div class="space-y-8">
  <div class="space-y-2">
    <h1 class="text-4xl font-bold tracking-tight">Project Portfolio</h1>
    <p class="text-muted-foreground text-lg">
      Explore {{ totalProjects() }} projects across {{ suites().length }} application suites
    </p>
  </div>

  <!-- Suite filter tabs -->
  <dw-tabs [value]="selectedSuite()" (valueChange)="selectedSuite.set($event)">
    <dw-tabs-list>
      <dw-tabs-trigger value="all">All ({{ totalProjects() }})</dw-tabs-trigger>
      @for (suite of suites(); track suite.id) {
        <dw-tabs-trigger [value]="suite.id">
          {{ suite.name }} ({{ suite.projects.length }})
        </dw-tabs-trigger>
      }
    </dw-tabs-list>

    <dw-tabs-content value="all">
      @for (suite of suites(); track suite.id) {
        <dw-suite-group [suite]="suite" />
      }
    </dw-tabs-content>

    @for (suite of suites(); track suite.id) {
      <dw-tabs-content [value]="suite.id">
        <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          @for (project of suite.projects; track project.id) {
            <dw-project-card [project]="project" />
          }
        </div>
      </dw-tabs-content>
    }
  </dw-tabs>
</div>
```

**State with signals:**
```typescript
export class ProjectsComponent {
  private projectService = inject(ProjectService);
  suites       = signal<Suite[]>([]);
  selectedSuite = signal<string>('all');
  totalProjects = computed(() => this.suites().reduce((sum, s) => sum + s.projects.length, 0));

  ngOnInit() {
    this.projectService.getSuites().subscribe(suites => this.suites.set(suites));
  }
}
```

---

### 7B — graph/ (Dark D3 — ported from JSX)

**Key Angular wrapper:**
```typescript
@Component({
  selector: 'dw-force-graph',
  standalone: true,
  template: `
    <div #container class="w-full h-full relative overflow-hidden">
      <svg #graphSvg class="w-full h-full"></svg>
    </div>
  `,
  host: { class: 'block w-full h-full' }
})
export class ForceGraphComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('container') container!: ElementRef<HTMLDivElement>;
  @ViewChild('graphSvg') svgEl!: ElementRef<SVGSVGElement>;

  graphData = input.required<GraphData>();
  activeNodeId = input<string | null>(null);
  nodeClick = output<GraphNode>();

  private renderer  = inject(D3RendererService);
  private simulation: d3.Simulation<GraphNode, GraphLink> | null = null;

  ngAfterViewInit() { this.render(); }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['graphData'] && !changes['graphData'].firstChange) {
      this.render();
    }
  }

  private render() {
    const { clientWidth: W, clientHeight: H } = this.container.nativeElement;
    this.simulation?.stop();
    this.simulation = this.renderer.render(
      this.svgEl.nativeElement,
      this.graphData(),
      W, H,
      (node) => this.nodeClick.emit(node)
    );
  }

  ngOnDestroy() { this.simulation?.stop(); }
}
```

**graph.component.ts — host with dark theme:**
```typescript
@Component({
  selector: 'dw-graph',
  standalone: true,
  template: `
    <!-- Full-screen dark graph view -->
    <div class="graph-mode flex flex-col h-screen overflow-hidden"
         style="background: #020C18; font-family: 'Courier New', monospace">

      <!-- Graph header (dark) -->
      <header class="graph-header">...</header>

      <!-- Main area -->
      <div class="flex-1 flex overflow-hidden relative">
        <dw-force-graph
          [graphData]="graphData()"
          [activeNodeId]="selected()?.id ?? null"
          (nodeClick)="onNodeClick($event)"
        />
        <dw-legend />
        @if (selected()) {
          <dw-info-panel [node]="selected()!" (close)="selected.set(null)" />
        }
      </div>

      <div class="graph-statusbar">...</div>
    </div>
  `
})
export class GraphComponent {
  private graphDataService = inject(GraphDataService);
  private projectService   = inject(ProjectService);

  suites   = signal<Suite[]>([]);
  level    = signal<GraphLevel>('cosmos');
  breadcrumb = signal<string[]>([]);
  selected = signal<GraphNode | null>(null);
  graphData = computed(() => {
    const W = window.innerWidth, H = window.innerHeight - 100;
    if (this.level() === 'cosmos') return this.graphDataService.buildCosmosGraph(this.suites(), W, H);
    if (this.level() === 'suite')  return this.graphDataService.buildSuiteGraph(this.breadcrumb()[0], this.suites(), W, H);
    return this.graphDataService.buildProjectGraph(this.breadcrumb()[1], this.suites(), W, H);
  });
}
```

---

### 7C — project-detail/ (Figma tabs)

**5 tabs matching Figma sections:**
```html
<!-- project-detail.component.html -->
<dw-tabs [value]="activeTab()" (valueChange)="activeTab.set($event)">
  <dw-tabs-list>
    <dw-tabs-trigger value="modules">
      <dw-icon name="package" /> Modules
    </dw-tabs-trigger>
    <dw-tabs-trigger value="apis">
      <dw-icon name="git-branch" /> API Catalog
    </dw-tabs-trigger>
    <dw-tabs-trigger value="ask">
      <dw-icon name="message-square" /> Ask DeepWiki
    </dw-tabs-trigger>
    <dw-tabs-trigger value="plan">
      <dw-icon name="flask-conical" /> Plan & Tests
    </dw-tabs-trigger>
    <dw-tabs-trigger value="compare">
      <dw-icon name="bar-chart-3" /> Live Comparison
    </dw-tabs-trigger>
  </dw-tabs-list>

  <dw-tabs-content value="modules">
    <dw-modules-section [project]="project()" />
  </dw-tabs-content>
  <dw-tabs-content value="apis">
    <dw-api-catalog-section [project]="project()" />
  </dw-tabs-content>
  <dw-tabs-content value="ask">
    <dw-ask-deepwiki-section [project]="project()" />
  </dw-tabs-content>
  <dw-tabs-content value="plan">
    <dw-plan-tests-section [project]="project()" />
  </dw-tabs-content>
  <dw-tabs-content value="compare">
    <dw-live-comparison-section [project]="project()" />
  </dw-tabs-content>
</dw-tabs>
```

### 7D — ask-deepwiki-section (real API call)

```typescript
@Component({ standalone: true, ... })
export class AskDeepwikiSectionComponent {
  project  = input.required<Project>();
  private wikiService = inject(WikiService);

  messages  = signal<Message[]>([]);
  input     = signal('');
  loading   = signal(false);
  error     = signal<string | null>(null);

  suggestedQuestions = computed(() => [
    `What authentication methods does ${this.project().name} support?`,
    `How does ${this.project().name} handle error scenarios?`,
    `What are the main modules in ${this.project().name}?`,
    `Explain the ${this.project().modules[0]?.name ?? 'main'} module`,
  ]);

  send(question?: string) {
    const text = question ?? this.input();
    if (!text.trim() || this.loading()) return;

    this.messages.update(m => [...m, { role: 'user', content: text }]);
    this.input.set('');
    this.loading.set(true);
    this.error.set(null);

    this.wikiService.ask({
      question: text,
      repo_id:  this.project().id,
    }).subscribe({
      next: (res) => {
        this.messages.update(m => [...m, { role: 'assistant', content: res.answer }]);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set('Failed to get answer. Is the API running?');
        this.loading.set(false);
      }
    });
  }
}
```

---

## 8. app.routes.ts

```typescript
export const routes: Routes = [
  {
    path: '',
    component: AppShellComponent,
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./features/projects/projects.component').then(m => m.ProjectsComponent),
      },
      {
        path: 'project/:id',
        loadComponent: () =>
          import('./features/project-detail/project-detail.component').then(m => m.ProjectDetailComponent),
      },
      {
        path: 'search',
        loadComponent: () =>
          import('./features/search/search.component').then(m => m.SearchComponent),
      },
    ]
  },
  {
    // Graph is full-screen dark mode — no app shell header
    path: 'graph',
    loadComponent: () =>
      import('./features/graph/graph.component').then(m => m.GraphComponent),
  },
  { path: '**', redirectTo: '' }
];
```

---

## 9. Header Component

```html
<!-- header.component.html — Figma design with graph toggle -->
<header class="sticky top-0 z-50 w-full border-b bg-primary text-primary-foreground">
  <div class="container flex h-16 items-center px-4">

    <a routerLink="/" class="flex items-center space-x-2">
      <lucide-icon name="layers" class="h-6 w-6 text-yellow-400" />
      <span class="font-bold text-xl">DeepWiki</span>
    </a>

    <nav class="ml-10 flex gap-6">
      <a routerLink="/" routerLinkActive="text-yellow-400"
         class="text-sm font-medium flex items-center gap-2">
        <lucide-icon name="layers" class="h-4 w-4" /> All Projects
      </a>
      <a routerLink="/search" routerLinkActive="text-yellow-400"
         class="text-sm font-medium flex items-center gap-2">
        <lucide-icon name="search" class="h-4 w-4" /> Search
      </a>
      <a routerLink="/graph" routerLinkActive="text-yellow-400"
         class="text-sm font-medium flex items-center gap-2">
        <lucide-icon name="share-2" class="h-4 w-4" /> Architecture Graph
      </a>
    </nav>

    <div class="ml-auto relative w-64">
      <lucide-icon name="search" class="absolute left-2.5 top-2.5 h-4 w-4 text-primary-foreground/60" />
      <input type="search" placeholder="Quick search..."
             class="pl-8 w-full h-10 rounded-md bg-primary-foreground/10 border border-primary-foreground/20
                    text-primary-foreground placeholder:text-primary-foreground/60 text-sm px-3 py-2"
             (keyup.enter)="onQuickSearch($event)" />
    </div>
  </div>
</header>
```

---

## 10. Build Iterations

### Iteration A — Setup + Shell (Days 1-2)
```
✅ ng new deepwiki-ui --standalone --routing --style=scss
✅ Tailwind configured with Figma + graph tokens
✅ Environment files (dev: localhost:8000, prod: Railway URL)
✅ AppShellComponent + HeaderComponent + FooterComponent
✅ Routing configured (4 routes, lazy loaded)
✅ All core models/interfaces created
✅ Service stubs with HttpClient
Done when: app loads at localhost:4200, routes navigate without errors
```

### Iteration B — Shared Component Library (Days 3-4)
```
✅ BadgeComponent (4 variants matching Figma)
✅ CardComponent (CardHeader, CardContent, CardTitle, CardDescription)
✅ ButtonComponent (default, outline, ghost, link)
✅ TabsComponent (TabsList, TabsTrigger, TabsContent)
✅ InputComponent + TextareaComponent
✅ ProgressComponent
✅ MethodColorPipe, TruncatePipe
Done when: Storybook-style test page shows all components styled correctly
```

### Iteration C — Projects Page (Days 5-6)
```
✅ ProjectsComponent with suite tabs
✅ ProjectCardComponent (Figma card design, hover states)
✅ SuiteGroupComponent (suite header + project grid)
✅ ProjectService.getSuites() returns mock data matching JSX structure
✅ Navigation to /project/:id on card click
Done when: Homepage shows all suites with project cards, tabs filter correctly
```

### Iteration D — D3 Graph (Days 7-9)
```
✅ GraphDataService: port buildCosmosGraph, buildSuiteGraph, buildProjectGraph from JSX
✅ D3RendererService: port all D3 rendering logic, run outside NgZone
✅ ForceGraphComponent: @ViewChild SVG container, calls D3RendererService
✅ GraphComponent: dark theme host, level/breadcrumb signals, computed graphData
✅ InfoPanelComponent: drill-down detail panel (ported from JSX InfoPanel)
✅ LegendComponent + ScanBarComponent
Done when: /graph shows Universe view with force simulation, click navigates levels
```

### Iteration E — Project Detail (Days 10-12)
```
✅ ProjectDetailComponent with 5-tab layout
✅ ModulesSectionComponent (module cards with feature lists)
✅ ApiCatalogSectionComponent (exposed/consumed tabs, method badges, search)
✅ StatsBarComponent (modules count, APIs count, relations count)
✅ RelationsSection (connected services list)
Done when: /project/any-id shows full detail with tabs
```

### Iteration F — AI Sections (Days 13-16)
```
✅ AskDeepwikiSectionComponent: real API call to FastAPI /ask
✅ Suggested questions, chat UI, loading state, error state
✅ PlanTestsSectionComponent: requirement input → /plan API → plan + tests display
✅ LiveComparisonSectionComponent: /compare API → before/after token comparison
✅ Error boundary: API offline → clear error message, not broken UI
Done when: Ask DeepWiki returns real answers from FastAPI backend
```

### Iteration G — Search + Polish (Days 17-19)
```
✅ SearchComponent: real-time filter, tech chip filters
✅ Global search in header → navigates to /search?q=...
✅ Loading skeletons on all data fetches
✅ Empty states for all pages
✅ Responsive: md/lg/xl grid layouts
✅ Error states (API down message)
✅ Page titles with Angular Title service
Done when: Full app works on mobile, all error states handled
```

---

## 11. What NOT to Build in Angular

```
⛔ Bring Streamlit code into Angular — rewrite cleanly
⛔ Use Angular Material — different design language from Figma
⛔ Use any React libraries — full Angular migration
⛔ Build own D3 wrapper library — D3RendererService is enough
⛔ NgRx state management — signals handle this scale
⛔ Server-side rendering (SSR) now — add later if SEO needed
⛔ Duplicate graph in card pages — /graph is its own route
⛔ Hard-code API responses — always go through service layer
```

---

## 12. Key Design Decisions

| Decision | What | Why |
|---|---|---|
| Standalone components | All components standalone, no NgModules | Angular 17 best practice, tree-shaking |
| Signals | State management with signals, not BehaviorSubject | Angular 17+, simpler async, auto-tracks |
| NgZone.runOutsideAngular | D3 simulation outside zone | D3 ticks every frame — would kill change detection |
| Lazy routing | All 4 routes lazy | Graph (D3 + d3 bundle) is heavy, don't load until needed |
| /graph is full-screen | Graph has no AppShell wrapper | Dark theme conflicts with light header/footer |
| Mock data first | ProjectService starts with JSX mock data | Wire real API after UI proven |
| Figma Tailwind tokens | Custom colors in tailwind.config.js | No runtime CSS-in-JS, all compiled |
| MethodColorPipe | GET/POST/DELETE colors as pipe | Reused in 3 places, consistent, testable |
| @if/@for syntax | New control flow, not *ngIf/*ngFor | Angular 17+, no extra imports, cleaner templates |

---

## 13. API Integration Map

| Feature | Angular Component | FastAPI Endpoint | Request | Response |
|---|---|---|---|---|
| Projects list | ProjectsComponent | GET /classes | — | ClassInfo[] |
| Stats | HeaderComponent | GET /stats | — | StatsResponse |
| Ask DeepWiki | AskDeepwikiSection | POST /ask | {question, repo_id} | {answer, sources} |
| Search | SearchComponent | POST /search | {query, top_k} | SearchResult[] |
| Flow trace | ModulesSection | POST /flow | {entry_point, repo_id} | FlowTrace |
| Plan + Tests | PlanTestsSection | POST /plan | {requirement, repo_id} | PlanResponse |
| Comparison | LiveComparisonSection | POST /compare | {query} | CompareResult |
| Architecture | GraphComponent | GET /architecture | — | MermaidDiagram |

---

## 14. File to Create First

Start here — creates the skeleton everything else attaches to:

```bash
ng new deepwiki-ui --standalone --routing --style=scss
cd deepwiki-ui
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init
npm install d3 @types/d3 lucide-angular

# Create the structure
ng g component layout/header --standalone --inline-template
ng g component layout/footer --standalone --inline-template
ng g component layout/app-shell --standalone
ng g service core/services/project
ng g service core/services/wiki
ng g service core/services/graph-data
ng g service core/services/d3-renderer
ng g component features/projects/projects --standalone
ng g component features/graph/graph --standalone
```

---

*This plan is complete. No ambiguity. Each iteration has a clear "done when" test.*  
*Start with Iteration A. Do not start Iteration B until A's "done when" passes.*
