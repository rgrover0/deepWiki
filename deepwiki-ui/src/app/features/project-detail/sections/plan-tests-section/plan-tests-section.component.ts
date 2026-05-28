import { Component, input, signal } from '@angular/core';
import { Project } from '../../../../core/models';
import { LucideAngularModule } from 'lucide-angular';

interface PlanResult {
  feature: string;
  implementation: string;
  testCases: string[];
}

@Component({
  selector: 'dw-plan-tests-section',
  standalone: true,
  imports: [LucideAngularModule],
  template: `
    <div class="space-y-6">
      <div class="rounded-xl border bg-card p-6 space-y-4">
        <div class="flex items-center gap-2">
          <lucide-icon name="flask-conical" class="h-5 w-5 text-primary"></lucide-icon>
          <h3 class="font-semibold text-lg">Feature Planning & Test Generation</h3>
        </div>
        <p class="text-sm text-muted-foreground">
          Describe a new feature and get an implementation plan with comprehensive test cases
        </p>

        @if (!result()) {
          <div class="space-y-2">
            <p class="text-sm text-muted-foreground">Example features:</p>
            <div class="flex flex-wrap gap-2">
              @for (ex of examples; track ex) {
                <button (click)="generate(ex)" [disabled]="generating()"
                  class="flex items-center gap-2 text-sm px-3 py-1.5 rounded-lg border hover:bg-muted transition-colors disabled:opacity-50">
                  <lucide-icon name="sparkles" class="h-3 w-3 text-accent"></lucide-icon>
                  {{ ex }}
                </button>
              }
            </div>
          </div>

          <div class="space-y-2">
            <textarea
              #ft
              (input)="featureText = ft.value"
              [value]="featureText"
              placeholder="Describe the feature you want to add..."
              [disabled]="generating()"
              rows="4"
              class="w-full min-h-[100px] rounded-lg border px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary resize-none disabled:opacity-50"
            ></textarea>
            <button
              (click)="generate(ft.value)"
              [disabled]="generating() || !ft.value.trim()"
              class="w-full flex items-center justify-center gap-2 h-10 rounded-lg bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50 transition-colors">
              @if (generating()) {
                Generating plan...
              } @else {
                <lucide-icon name="code" class="h-4 w-4"></lucide-icon>
                Generate Implementation Plan & Tests
              }
            </button>
          </div>
        }

        @if (result(); as r) {
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <h4 class="text-lg font-semibold">Feature: {{ r.feature }}</h4>
              <button (click)="reset()"
                class="text-sm px-3 py-1.5 rounded-lg border hover:bg-muted transition-colors">
                New Feature
              </button>
            </div>

            <!-- Result sub-tabs -->
            <div class="border-b flex">
              <button (click)="resultTab.set('plan')" [class]="tabClass(resultTab() === 'plan')">
                Implementation Plan
              </button>
              <button (click)="resultTab.set('tests')" [class]="tabClass(resultTab() === 'tests')">
                Test Cases
              </button>
            </div>

            @if (resultTab() === 'plan') {
              <div class="rounded-xl border bg-card p-6 space-y-3">
                <h4 class="font-semibold text-base">Implementation Steps</h4>
                <pre class="bg-muted p-4 rounded-lg overflow-x-auto text-sm font-mono whitespace-pre-wrap"><code>{{ r.implementation }}</code></pre>
              </div>
            }

            @if (resultTab() === 'tests') {
              <div class="rounded-xl border bg-card p-6 space-y-3">
                <h4 class="font-semibold text-base">Test Cases</h4>
                <p class="text-sm text-muted-foreground">{{ r.testCases.length }} test cases generated</p>
                <div class="space-y-3">
                  @for (tc of r.testCases; track tc; let i = $index) {
                    <div class="flex items-start gap-3 p-3 bg-muted rounded-lg">
                      <lucide-icon name="check-circle-2" class="h-5 w-5 text-primary flex-shrink-0 mt-0.5"></lucide-icon>
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
      </div>
    </div>
  `,
})
export class PlanTestsSectionComponent {
  project = input.required<Project>();

  featureText = '';
  generating  = signal(false);
  result      = signal<PlanResult | null>(null);
  resultTab   = signal<'plan' | 'tests'>('plan');

  readonly examples = [
    'Add rate limiting to API endpoints',
    'Implement caching layer for frequently accessed data',
    'Add audit logging for sensitive operations',
  ];

  generate(text: string): void {
    const t = text.trim();
    if (!t || this.generating()) return;
    this.featureText = '';
    this.generating.set(true);
    setTimeout(() => {
      const p   = this.project();
      const cls = t.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('');
      this.result.set({
        feature: t,
        implementation: [
          `// Step 1: Define the ${t} interface`,
          `interface ${cls}Config {`,
          `  enabled: boolean;`,
          `  settings: Record<string, unknown>;`,
          `}`,
          ``,
          `// Step 2: Implement in ${p.modules[0]?.name ?? 'core module'}`,
          `class ${cls}Service {`,
          `  constructor(private config: ${cls}Config) {}`,
          ``,
          `  async execute(params: unknown): Promise<unknown> {`,
          `    // Integration with ${p.techStack[0] ?? 'existing stack'}`,
          `    // Connect to ${p.modules[0]?.name ?? 'core module'}`,
          `  }`,
          `}`,
          ``,
          `// Step 3: Add middleware / integration points`,
          `// - Update API endpoints`,
          `// - Add monitoring and logging`,
          ``,
          `// Step 4: Database migrations (if needed)`,
          `// - Using ${p.techStack.find(s => s.includes('SQL') || s.includes('Mongo')) ?? 'database'}`,
          ``,
          `// Step 5: Configuration`,
          `// - Environment variables`,
          `// - Feature flags`,
          `// - Documentation updates`,
        ].join('\n'),
        testCases: [
          `Verify ${t} works correctly with valid input parameters`,
          `Test ${t} handles invalid input gracefully with appropriate error messages`,
          `Ensure ${t} integrates properly with ${p.modules[0]?.name ?? 'existing modules'}`,
          `Validate ${t} performance under high load conditions`,
          `Test ${t} rollback and error recovery scenarios`,
          `Verify ${t} does not break existing functionality (regression tests)`,
          `Test ${t} with edge cases and boundary conditions`,
          `Ensure ${t} logs and monitoring are working correctly`,
        ],
      });
      this.generating.set(false);
    }, 1500);
  }

  reset(): void {
    this.result.set(null);
    this.featureText = '';
    this.resultTab.set('plan');
  }

  tabClass(active: boolean): string {
    const base = 'px-4 py-2 text-sm font-medium -mb-px border-b-2 transition-colors';
    return active
      ? `${base} border-primary text-primary`
      : `${base} border-transparent text-muted-foreground hover:text-foreground`;
  }
}
