# DeepWiki Angular — Figma Delta Report
> Source analysed: `rgrover0/Projectwikiwebsitedesign` (React/TSX)  
> Target: `dw-angular/` (Angular 17+)  
> Purpose: Apply every remaining design change so Angular exactly matches the Figma

---

## How to Use This File

Each section names the **file to edit**, shows the **Figma original**, shows the **current Angular code**, and gives the **exact fix**.  
Changes are ordered largest → smallest impact. Apply all of them.

---

## Delta 1 — `api-catalog.component` (largest structural gap)

### 1A — Missing stat-cards row (3 summary cards above tabs)

**Figma** renders a 3-card summary grid before the tab list:

```tsx
<div className="grid gap-4 md:grid-cols-3">
  <Card className="bg-primary/5">
    <CardHeader className="pb-3">
      <CardTitle className="text-sm font-medium">Total APIs</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{project.apis.length}</div>
    </CardContent>
  </Card>
  <Card className="bg-green-50">
    <CardHeader className="pb-3">
      <CardTitle className="text-sm font-medium flex items-center gap-2">
        <ArrowUpFromLine className="h-4 w-4" /> Exposed
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{exposedApis.length}</div>
    </CardContent>
  </Card>
  <Card className="bg-blue-50">
    <CardHeader className="pb-3">
      <CardTitle className="text-sm font-medium flex items-center gap-2">
        <ArrowDownToLine className="h-4 w-4" /> Consumed
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{consumedApis.length}</div>
    </CardContent>
  </Card>
</div>
```

**Current Angular** — missing entirely.

**Fix — add to `api-catalog.component.html`** after the search input, before the tabs:

```html
<!-- API summary stat cards -->
<div class="grid gap-4 md:grid-cols-3">
  <div class="card p-4 bg-primary/5 space-y-1">
    <p class="text-sm font-medium">Total APIs</p>
    <p class="text-2xl font-bold">{{ project.apis.length }}</p>
  </div>
  <div class="card p-4 bg-green-50 space-y-1">
    <p class="text-sm font-medium flex items-center gap-2">
      <lucide-angular [img]="UpIcon" class="h-4 w-4" /> Exposed
    </p>
    <p class="text-2xl font-bold">{{ exposed.length }}</p>
  </div>
  <div class="card p-4 bg-blue-50 space-y-1">
    <p class="text-sm font-medium flex items-center gap-2">
      <lucide-angular [img]="DownIcon" class="h-4 w-4" /> Consumed
    </p>
    <p class="text-2xl font-bold">{{ consumed.length }}</p>
  </div>
</div>
```

---

### 1B — Missing third tab ("All APIs")

**Figma** has **3 tabs**: `All APIs (N)` | `Exposed (N)` | `Consumed (N)`.  
**Current Angular** has only 2 tabs.

**Fix — `api-catalog.component.ts`**

```typescript
// Change type from 'exposed'|'consumed' to include 'all'
tab = signal<'all' | 'exposed' | 'consumed'>('all');

// Add computed for all-tab list
get all()     { return this.filter(this.project.apis); }
get exposed() { return this.filter(this.project.apis.filter(a => a.type === 'exposed')); }
get consumed(){ return this.filter(this.project.apis.filter(a => a.type === 'consumed')); }

get list() {
  switch (this.tab()) {
    case 'exposed':  return this.exposed;
    case 'consumed': return this.consumed;
    default:         return this.all;
  }
}
```

**Fix — `api-catalog.component.html`** (replace tab bar):

```html
<div class="tab-bar grid grid-cols-3">
  <button [class]="tab() === 'all'      ? 'tab-trigger active' : 'tab-trigger'" (click)="tab.set('all')">
    All APIs ({{ project.apis.length }})
  </button>
  <button [class]="tab() === 'exposed'  ? 'tab-trigger active' : 'tab-trigger'" (click)="tab.set('exposed')">
    Exposed ({{ exposed.length }})
  </button>
  <button [class]="tab() === 'consumed' ? 'tab-trigger active' : 'tab-trigger'" (click)="tab.set('consumed')">
    Consumed ({{ consumed.length }})
  </button>
</div>
```

---

### 1C — Card title + description text mismatch

| Location | Figma | Current Angular |
|---|---|---|
| `CardTitle` | `API Catalog` | `API Catalog — {{ project.name }}` |
| `CardDescription` | `Browse all APIs exposed and consumed by {{ project.name }}` | `Complete API registry…` |

**Fix — `api-catalog.component.html`**:

```html
<!-- Change header section to: -->
<h3 class="font-semibold text-lg">API Catalog</h3>
...
<p class="text-sm text-muted-foreground mb-4">
  Browse all APIs exposed and consumed by {{ project.name }}
</p>
```

---

### 1D — Empty state message

**Figma**: `No APIs found matching "{searchQuery}"` (dynamic message)  
**Current Angular**: `No APIs match your search.` (static)

**Fix — `api-catalog.component.html`** `@empty` block:

```html
@empty {
  <p class="text-center py-8 text-muted-foreground">
    @if (query) {
      No APIs found matching "{{ query }}"
    } @else {
      No APIs found
    }
  </p>
}
```

---

## Delta 2 — `live-comparison.component` (structural + content gaps)

### 2A — Missing "Optimization Strategies" card (entire bottom section)

**Figma** renders a fourth card below the metric cards:

```tsx
<Card>
  <CardHeader>
    <CardTitle className="text-base">Optimization Strategies Applied</CardTitle>
  </CardHeader>
  <CardContent>
    <ul className="space-y-3">
      <li className="flex items-start gap-3">
        <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
          <span className="text-xs font-bold text-primary">1</span>
        </div>
        <div>
          <p className="font-medium">Prompt Caching</p>
          <p className="text-sm text-muted-foreground">
            Cached common prompt patterns to reduce redundant token processing
          </p>
        </div>
      </li>
      <!-- 3 more items: Response Compression, Smart Context Management, Batch Processing -->
    </ul>
  </CardContent>
</Card>
```

**Current Angular** — missing entirely.

**Fix — add to `live-comparison.component.html`** after the `@for` metrics loop:

```html
<!-- Optimization strategies card -->
<div class="card p-6">
  <h4 class="font-semibold text-base mb-4">Optimization Strategies Applied</h4>
  <ul class="space-y-3">
    @for (strategy of strategies; track strategy.title) {
      <li class="flex items-start gap-3">
        <div class="strategy-num">{{ $index + 1 }}</div>
        <div>
          <p class="font-medium">{{ strategy.title }}</p>
          <p class="text-sm text-muted-foreground">{{ strategy.desc }}</p>
        </div>
      </li>
    }
  </ul>
</div>
```

**Fix — add to `live-comparison.component.ts`**:

```typescript
readonly strategies = [
  { title: 'Prompt Caching',         desc: 'Cached common prompt patterns to reduce redundant token processing' },
  { title: 'Response Compression',   desc: 'Optimized response formats to minimize token output without losing information' },
  { title: 'Smart Context Management', desc: 'Reduced context window size by intelligently selecting relevant information' },
  { title: 'Batch Processing',       desc: 'Grouped related queries to reduce API call overhead' },
];
```

**Fix — add to `live-comparison.component.scss`**:

```scss
.strategy-num {
  @apply h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center
         flex-shrink-0 mt-0.5 text-xs font-bold text-primary;
}
```

---

### 2B — Progress bars: two bars per metric (not one)

**Figma** renders **two** progress bars per metric — before (100%) and after (reduced %):

```tsx
<Progress value={100} className="h-2 bg-muted" />          // before = full
<Progress value={(metric.after / metric.before) * 100} className="h-2" />  // after = reduced
```

**Current Angular** shows one bar representing the improvement % (wrong).

**Fix — `live-comparison.component.html`** inside the metric `@for` loop:

```html
<!-- Replace the single progress-track div with: -->
<div class="space-y-2">
  <div class="flex items-center justify-between text-sm">
    <span class="text-muted-foreground">Before optimisation</span>
    <span class="font-medium">{{ m.before | number }} {{ m.unit }}</span>
  </div>
  <div class="progress-track">
    <div class="progress-fill" style="width: 100%"></div>
  </div>

  <div class="flex items-center justify-between text-sm">
    <span class="text-muted-foreground">After optimisation</span>
    <span class="font-medium text-primary">{{ m.after | number }} {{ m.unit }}</span>
  </div>
  <div class="progress-track">
    <div class="progress-fill"
         [style.width.%]="(m.after / m.before) * 100"></div>
  </div>
</div>
```

Add `DecimalPipe` to the component imports:

```typescript
import { DecimalPipe } from '@angular/common';
// add DecimalPipe to imports array
```

---

### 2C — Improvement badge: TrendingDown icon + text

**Figma**:
```tsx
<Badge className="bg-green-100 text-green-700">
  <TrendingDown className="h-3 w-3 mr-1" />
  {metric.improvement}% improved
</Badge>
```

**Current Angular**: plain green text span, no icon, says "% improvement".

**Fix — `live-comparison.component.ts`**: add `TrendingDown` icon import:

```typescript
import { LucideAngularModule, BarChart3, Zap, DollarSign, TrendingDown } from 'lucide-angular';
readonly TrendingDownIcon = TrendingDown;
```

**Fix — `live-comparison.component.html`** (replace improvement span):

```html
<span class="improvement">
  <lucide-angular [img]="TrendingDownIcon" class="h-3 w-3" />
  {{ m.improvement }}% improved
</span>
```

**Fix — `live-comparison.component.scss`**:

```scss
.improvement {
  @apply flex items-center gap-1 text-green-700 text-xs font-medium
         bg-green-100 px-2 py-0.5 rounded;
}
```

---

### 2D — Cost savings: calculated, not hard-coded

**Figma** calculates dynamically: `$(before - after)/mo`  
**Current Angular** hard-codes `$2,050/mo`

**Fix — `live-comparison.component.ts`**:

```typescript
// Add computed getters
get tokenSavingsMetric() { return this.metrics.find(m => m.label === 'Token Usage per Request')!; }
get costMetric()         { return this.metrics.find(m => m.label === 'Monthly API Cost')!; }
get costSaving()         { return (this.costMetric.before - this.costMetric.after).toLocaleString(); }
```

**Fix — `live-comparison.component.html`** (summary boxes):

```html
<!-- Token savings box -->
<div class="text-3xl font-bold text-primary">{{ tokenSavingsMetric.improvement }}%</div>
<p class="text-xs text-muted-foreground">
  {{ tokenSavingsMetric.before.toLocaleString() }} →
  {{ tokenSavingsMetric.after.toLocaleString() }} tokens
</p>

<!-- Cost savings box -->
<div class="text-3xl font-bold text-accent">${{ costSaving }}/mo</div>
<p class="text-xs text-muted-foreground">{{ costMetric.improvement }}% reduction</p>
```

---

## Delta 3 — `plan-tests.component` (result view structure)

### 3A — Result view: two sub-tabs (Plan / Tests), not sequential

**Figma** shows a **tabbed result** view with two tabs:

```tsx
<Tabs defaultValue="plan">
  <TabsList className="grid w-full grid-cols-2">
    <TabsTrigger value="plan">Implementation Plan</TabsTrigger>
    <TabsTrigger value="tests">Test Cases</TabsTrigger>
  </TabsList>
  <TabsContent value="plan">
    <Card>
      <CardHeader><CardTitle>Implementation Steps</CardTitle></CardHeader>
      <CardContent>
        <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
          <code>{result.implementation}</code>
        </pre>
      </CardContent>
    </Card>
  </TabsContent>
  <TabsContent value="tests">
    <Card>
      <CardHeader>
        <CardTitle>Test Cases</CardTitle>
        <CardDescription>{result.testCases.length} test cases generated</CardDescription>
      </CardHeader>
      <CardContent>
        <!-- test cases with "Test Case N" label -->
      </CardContent>
    </Card>
  </TabsContent>
</Tabs>
```

**Current Angular** shows them sequentially (no sub-tabs).

**Fix — `plan-tests.component.ts`**: add `resultTab` signal and update result model:

```typescript
resultTab = signal<'plan' | 'tests'>('plan');

// Rename field: plan → implementation (matches Figma model)
// Update the result type:
interface PlanResult {
  feature:        string;
  implementation: string;   // was 'plan'
  testCases:      string[]; // was 'tests'
}

// Update generate() to use implementation field
this.result.set({
  feature:        text,
  implementation: `// Step 1: Define the interface\n...`,
  testCases:      [...],
});
```

**Fix — `plan-tests.component.html`** result block:

```html
@if (result(); as r) {
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h4 class="text-lg font-semibold">Feature: {{ r.feature }}</h4>
      <button class="btn-outline text-sm px-3 py-1.5" (click)="reset()">New Feature</button>
    </div>

    <!-- Result sub-tabs -->
    <div class="tab-bar grid grid-cols-2">
      <button [class]="resultTab() === 'plan'  ? 'tab-trigger active' : 'tab-trigger'"
              (click)="resultTab.set('plan')">Implementation Plan</button>
      <button [class]="resultTab() === 'tests' ? 'tab-trigger active' : 'tab-trigger'"
              (click)="resultTab.set('tests')">Test Cases</button>
    </div>

    @if (resultTab() === 'plan') {
      <div class="card p-6">
        <h4 class="font-semibold text-base mb-3">Implementation Steps</h4>
        <pre class="plan-block overflow-x-auto"><code>{{ r.implementation }}</code></pre>
      </div>
    }

    @if (resultTab() === 'tests') {
      <div class="card p-6 space-y-3">
        <h4 class="font-semibold text-base">Test Cases</h4>
        <p class="text-sm text-muted-foreground">{{ r.testCases.length }} test cases generated</p>
        <div class="space-y-3">
          @for (tc of r.testCases; track tc; let i = $index) {
            <div class="flex items-start gap-3 p-3 bg-muted rounded-lg">
              <lucide-angular [img]="CheckIcon" class="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
              <div>
                <p class="text-sm font-medium mb-1">Test Case {{ i + 1 }}</p>
                <p class="text-sm text-muted-foreground">{{ tc }}</p>
              </div>
            </div>
          }
        </div>
      </div>
    }
  </div>
}
```

---

### 3B — Generate button: icon + text + width

| | Figma | Current Angular |
|---|---|---|
| Icon | `<Code />` | `<Sparkles />` |
| Text | `Generate Implementation Plan & Tests` | `Generate Plan & Tests` |
| Width | `w-full` | not full width |

**Fix — `plan-tests.component.html`** (generate button):

```html
<button class="gen-btn w-full justify-center" [disabled]="generating() || !featureText.trim()"
        (click)="generate()">
  @if (generating()) {
    Generating plan…
  } @else {
    <lucide-angular [img]="CodeIcon" class="h-4 w-4" />
    Generate Implementation Plan & Tests
  }
</button>
```

**Fix — `plan-tests.component.ts`**: import `Code` icon:

```typescript
import { LucideAngularModule, FlaskConical, Sparkles, CheckCircle2, Code } from 'lucide-angular';
readonly CodeIcon = Code;
```

---

### 3C — Textarea minimum height

**Figma**: `className="min-h-[100px]"` on the Textarea  
**Current Angular**: `rows="3"` (~72px, too short)

**Fix — `plan-tests.component.scss`**:

```scss
.feature-input {
  // Add to existing styles:
  min-height: 100px;
}
```

---

### 3D — Implementation plan uses actual code, not prose

**Figma** `generateMockPlan()` outputs a TypeScript interface + class skeleton with real code formatting. Current Angular outputs plain numbered prose.

**Fix — `plan-tests.component.ts`** `generate()` method:

```typescript
generate(ex?: string): void {
  const text = (ex ?? this.featureText).trim();
  if (!text || this.generating()) return;
  this.featureText = '';
  this.generating.set(true);
  setTimeout(() => {
    const className = text.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('');
    this.result.set({
      feature: text,
      implementation:
`// Step 1: Define the ${text} interface
interface ${className}Config {
  enabled: boolean;
  settings: Record<string, unknown>;
}

// Step 2: Implement in ${this.project.modules[0]?.name ?? 'core module'}
class ${className}Service {
  constructor(private config: ${className}Config) {}

  async execute(params: unknown): Promise<unknown> {
    // Integration with ${this.project.techStack[0] ?? 'existing stack'}
    // Connect to ${this.project.modules[0]?.name ?? 'core module'}
  }
}

// Step 3: Add middleware / integration points
// - Update API endpoints
// - Add monitoring and logging

// Step 4: Database migrations (if needed)
// - Using ${this.project.techStack.find(t => t.includes('SQL') || t.includes('Mongo')) ?? 'database'}

// Step 5: Configuration
// - Environment variables
// - Feature flags
// - Documentation updates`,
      testCases: [
        `Verify ${text} works correctly with valid input parameters`,
        `Test ${text} handles invalid input gracefully with appropriate error messages`,
        `Ensure ${text} integrates properly with ${this.project.modules[0]?.name ?? 'existing modules'}`,
        `Validate ${text} performance under high load conditions`,
        `Test ${text} rollback and error recovery scenarios`,
        `Verify ${text} does not break existing functionality (regression tests)`,
        `Test ${text} with edge cases and boundary conditions`,
        `Ensure ${text} logs and monitoring are working correctly`,
      ],
    });
    this.generating.set(false);
  }, 1500);
}
```

---

## Delta 4 — `ask-deepwiki.component` (content and behaviour)

### 4A — Loading state: "Thinking…" text, not animated dots

**Figma**:
```tsx
<div className="bg-muted rounded-lg px-4 py-3">
  <p className="text-sm text-muted-foreground">Thinking...</p>
</div>
```

**Current Angular**: three animated dots.

**Fix — `ask-deepwiki.component.html`** (loading block):

```html
@if (loading()) {
  <div class="flex justify-start">
    <div class="msg msg-ai">
      <p class="text-sm text-muted-foreground">Thinking...</p>
    </div>
  </div>
}
```

Remove the dot animation classes from `ask-deepwiki.component.scss` (no longer needed):

```scss
// DELETE these rules:
// .dot-shape, .dot-1, .dot-2, .dot-3, @keyframes chat-dot
```

---

### 4B — Message text: whitespace-pre-wrap

**Figma**: `<p className="text-sm whitespace-pre-wrap">`  
**Current Angular**: `text-sm` only (multi-line responses collapse).

**Fix — `ask-deepwiki.component.html`**:

```html
<div [class]="m.role === 'user' ? 'msg msg-user' : 'msg msg-ai'">
  <p class="text-sm whitespace-pre-wrap">{{ m.content }}</p>
</div>
```

---

### 4C — Context-aware mock responses

**Figma** `generateMockResponse()` examines question keywords to return relevant answers about auth, modules, dependencies, tech stack. Current Angular returns a generic project summary.

**Fix — `ask-deepwiki.component.ts`** (replace `send()` timeout body):

```typescript
send(q?: string): void {
  const text = (q ?? this.input).trim();
  if (!text || this.loading()) return;
  this.messages.update(m => [...m, { role: 'user', content: text }]);
  this.input = '';
  this.loading.set(true);

  setTimeout(() => {
    this.messages.update(m => [...m, {
      role: 'assistant',
      content: this.generateResponse(text),
    }]);
    this.loading.set(false);
  }, 1000);
}

private generateResponse(question: string): string {
  const q = question.toLowerCase();

  if (q.includes('auth') || q.includes('authentication')) {
    const authModules = this.project.modules
      .filter(m => m.name.toLowerCase().includes('auth') || m.name.toLowerCase().includes('oauth'));
    if (authModules.length) {
      return authModules.map(m =>
        `${m.name}: ${m.description}\n  - ${m.features.join('\n  - ')}`
      ).join('\n\n');
    }
    return 'Standard authentication flows with JWT tokens and session management.';
  }

  if (q.includes('module') || q.includes('feature')) {
    const named = this.project.modules.find(m => q.includes(m.name.toLowerCase()));
    if (named) {
      return `${named.name} module in ${this.project.name}:\n\n${named.description}\n\nKey Features:\n${named.features.map(f => `• ${f}`).join('\n')}`;
    }
  }

  if (q.includes('dependenc') || q.includes('depend')) {
    const deps = this.project.relations.filter(r => r.type === 'depends-on');
    return deps.length
      ? `${this.project.name} depends on:\n\n${deps.map(d => `• ${d.projectName}: ${d.description}`).join('\n')}`
      : `${this.project.name} operates independently with minimal external dependencies.`;
  }

  if (q.includes('tech') || q.includes('stack') || q.includes('technolog')) {
    return `${this.project.name} is built using:\n\n${this.project.techStack.map(t => `• ${t}`).join('\n')}\n\nThis stack was chosen for its scalability, performance, and developer experience.`;
  }

  return `${this.project.name} is ${this.project.description}\n\nIt consists of ${this.project.modules.length} main modules:\n${this.project.modules.map(m => `• ${m.name}: ${m.description}`).join('\n')}\n\nThe project has ${this.project.relations.length} integrations with other services.`;
}
```

---

## Delta 5 — `projects.component` (card rendering gap)

### 5A — Single-suite tab: no Docs badge

**Figma** — on the single-suite tab, project cards render **without** the Docs badge (only `ArrowRight`):

```tsx
// In the per-suite TabsContent — no Docs badge
<div className="flex items-start justify-between">
  <Layers className="h-8 w-8 text-primary mb-2" />
  <ArrowRight ... />
</div>
```

**Current Angular** uses the same `#card` template for both tabs (always shows Docs badge).

**Fix — `projects.component.html`**: use a separate `#cardSuite` template for the single-suite tab that omits the badge:

```html
<!-- In the 'all' tab: use full card template (with Docs badge) -->
<ng-container [ngTemplateOutlet]="cardFull" [ngTemplateOutletContext]="{ p }" />

<!-- In the single-suite tab: use minimal card (no Docs badge) -->
<ng-container [ngTemplateOutlet]="cardSimple" [ngTemplateOutletContext]="{ p }" />

<ng-template #cardFull let-p="p">
  <!-- current #card template — unchanged -->
</ng-template>

<ng-template #cardSimple let-p="p">
  <!-- same as cardFull but without the hasDocs() condition and badge -->
  <article class="project-card group">
    <div class="flex items-start justify-between mb-2">
      <lucide-angular [img]="LayersIcon" class="h-8 w-8 text-primary" />
      <lucide-angular [img]="ArrowRightIcon"
        class="h-5 w-5 text-muted-foreground group-hover:text-accent transition-colors" />
    </div>
    <!-- rest identical to cardFull -->
  </article>
</ng-template>
```

---

### 5B — Layers icon on project card has `mb-2`

**Figma**: `<Layers className="h-8 w-8 text-primary mb-2" />`  
**Current Angular**: `class="h-8 w-8 text-primary"` (missing `mb-2`)

**Fix — `projects.component.html`**:

```html
<lucide-angular [img]="LayersIcon" class="h-8 w-8 text-primary mb-2" />
```

---

## Delta 6 — `layout.component` (minor)

### 6A — Logo: `space-x-2` not `gap-2`

**Figma**: `<Link className="flex items-center space-x-2">`  
**Current Angular**: uses `gap-2`.

Both render identically in modern browsers, but to match exactly:

**Fix — `layout.component.html`**:

```html
<a routerLink="/" class="flex items-center space-x-2 text-primary-foreground">
```

---

### 6B — Quick search placeholder punctuation

**Figma**: `placeholder="Quick search..."`  (3 ASCII dots)  
**Current Angular**: `placeholder="Quick search…"` (Unicode ellipsis)

**Fix — `layout.component.html`**:

```html
<input type="search" placeholder="Quick search..." class="quick-search" />
```

---

## Delta 7 — `search.component` (search input icon offset)

### 7A — Search icon position

**Figma**: `<Search className="absolute left-3 top-3 h-5 w-5">`  
**Current Angular**: `left-3 top-3.5` (3.5 instead of 3)

**Fix — `search.component.html`**:

```html
<lucide-angular [img]="SearchIcon"
  class="absolute left-3 top-3 h-5 w-5 text-muted-foreground pointer-events-none" />
```

---

## Delta 8 — `project-detail.component` (back button style)

### 8A — Back button is `<Button variant="ghost">`

**Figma**: `<Button variant="ghost" asChild className="mb-4">` with specific padding.  
**Current Angular**: plain anchor with custom `.btn-ghost` — has no bottom margin on the button.

**Fix — `project-detail.component.html`**:

```html
<a routerLink="/" class="btn-ghost mb-4 inline-flex">
  <lucide-angular [img]="ArrowLeftIcon" class="h-4 w-4 mr-2" />
  Back to Projects
</a>
```

Note `mr-2` on the icon (Figma uses `mr-2`, not `gap-2`).

**Fix — `project-detail.component.scss`**:

```scss
.btn-ghost {
  @apply inline-flex items-center rounded-md px-4 py-2 text-sm font-medium
         hover:bg-muted transition-colors;
}
```

---

## Delta 9 — `styles.scss` (missing DecimalPipe import, number formatting)

Figma uses `.toLocaleString()` on all metric numbers. Angular needs `DecimalPipe` added to the components that show formatted numbers.

**Fix** — add to `live-comparison.component.ts`:

```typescript
import { DecimalPipe } from '@angular/common';

@Component({
  imports: [LucideAngularModule, DecimalPipe],
  ...
})
```

Then use `| number` pipe in template:

```html
{{ m.before | number }} {{ m.unit }}
{{ m.after  | number }} {{ m.unit }}
```

---

## Summary Table

| # | File | Change type | Priority |
|---|---|---|---|
| 1A | `api-catalog.component.html` | Add 3 stat cards above tabs | 🔴 High |
| 1B | `api-catalog.component.*` | Add "All APIs" third tab | 🔴 High |
| 1C | `api-catalog.component.html` | Fix title + description text | 🟡 Medium |
| 1D | `api-catalog.component.html` | Fix empty state message | 🟢 Low |
| 2A | `live-comparison.component.*` | Add strategies card (4 items) | 🔴 High |
| 2B | `live-comparison.component.html` | Two progress bars per metric | 🔴 High |
| 2C | `live-comparison.component.*` | TrendingDown icon in badge | 🟡 Medium |
| 2D | `live-comparison.component.*` | Calculate cost savings dynamically | 🟡 Medium |
| 3A | `plan-tests.component.*` | Add Plan/Tests sub-tabs on result | 🔴 High |
| 3B | `plan-tests.component.html` | Code icon + full button text + w-full | 🟡 Medium |
| 3C | `plan-tests.component.scss` | Textarea min-height 100px | 🟢 Low |
| 3D | `plan-tests.component.ts` | Real code output in implementation | 🟡 Medium |
| 4A | `ask-deepwiki.component.html` | "Thinking..." not animated dots | 🟡 Medium |
| 4B | `ask-deepwiki.component.html` | `whitespace-pre-wrap` on message text | 🟢 Low |
| 4C | `ask-deepwiki.component.ts` | Context-aware mock responses | 🟡 Medium |
| 5A | `projects.component.html` | No Docs badge on single-suite tab | 🟢 Low |
| 5B | `projects.component.html` | `mb-2` on Layers icon in card | 🟢 Low |
| 6A | `layout.component.html` | `space-x-2` on logo link | 🟢 Low |
| 6B | `layout.component.html` | ASCII `...` not Unicode `…` in placeholder | 🟢 Low |
| 7A | `search.component.html` | Search icon `top-3` not `top-3.5` | 🟢 Low |
| 8A | `project-detail.component.*` | Back button `mb-4` + `mr-2` on icon | 🟢 Low |
| 9  | `live-comparison.component.ts` | Add `DecimalPipe` for number formatting | 🟡 Medium |

**Apply 🔴 High first** — they change visible structure.  
**Then 🟡 Medium** — they change content and behaviour.  
**Then 🟢 Low** — they match pixel-level styling.
