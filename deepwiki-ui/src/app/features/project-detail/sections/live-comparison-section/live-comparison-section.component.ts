import { Component, input } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { Project } from '../../../../core/models';
import { LucideAngularModule } from 'lucide-angular';

interface Metric {
  label: string;
  before: number;
  after: number;
  unit: string;
  improvement: number;
}

interface Strategy {
  title: string;
  desc: string;
}

@Component({
  selector: 'dw-live-comparison-section',
  standalone: true,
  imports: [LucideAngularModule, DecimalPipe],
  template: `
    <div class="space-y-6">

      <!-- Summary card -->
      <div class="rounded-xl border bg-gradient-to-br from-accent/5 to-primary/5 p-6 space-y-4">
        <div class="flex items-center gap-2">
          <lucide-icon name="bar-chart-3" class="h-5 w-5 text-primary"></lucide-icon>
          <h3 class="font-semibold text-lg">Performance & Cost Optimization</h3>
        </div>
        <p class="text-sm text-muted-foreground">
          Real-time comparison of token usage and cost savings with AI-powered optimizations
        </p>
        <div class="grid gap-4 md:grid-cols-2">
          <div class="bg-background rounded-lg p-6 space-y-2">
            <div class="flex items-center gap-2 text-muted-foreground text-sm">
              <lucide-icon name="zap" class="h-4 w-4"></lucide-icon>
              Token Savings
            </div>
            <div class="text-3xl font-bold text-primary">{{ tokenMetric.improvement }}%</div>
            <p class="text-xs text-muted-foreground">
              {{ tokenMetric.before | number }} → {{ tokenMetric.after | number }} tokens
            </p>
          </div>
          <div class="bg-background rounded-lg p-6 space-y-2">
            <div class="flex items-center gap-2 text-muted-foreground text-sm">
              <lucide-icon name="dollar-sign" class="h-4 w-4"></lucide-icon>
              Cost Savings
            </div>
            <div class="text-3xl font-bold text-accent">{{ '$' + costSaving }}/mo</div>
            <p class="text-xs text-muted-foreground">{{ costMetric.improvement }}% reduction</p>
          </div>
        </div>
      </div>

      <!-- Metric cards -->
      @for (m of metrics; track m.label) {
        <div class="rounded-xl border bg-card p-6 space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h4 class="font-semibold">{{ m.label }}</h4>
              <p class="text-sm text-muted-foreground">
                {{ m.before | number }} → {{ m.after | number }} {{ m.unit }}
              </p>
            </div>
            <span class="inline-flex items-center gap-1 text-xs font-medium bg-green-100 text-green-700 px-2 py-0.5 rounded">
              <lucide-icon name="trending-down" class="h-3 w-3"></lucide-icon>
              {{ m.improvement }}% improved
            </span>
          </div>

          <div class="space-y-2">
            <div class="flex items-center justify-between text-sm">
              <span class="text-muted-foreground">Before optimisation</span>
              <span class="font-medium">{{ m.before | number }} {{ m.unit }}</span>
            </div>
            <div class="h-2 rounded-full bg-muted overflow-hidden">
              <div class="h-full rounded-full bg-muted-foreground/30" style="width:100%"></div>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-muted-foreground">After optimisation</span>
              <span class="font-medium text-primary">{{ m.after | number }} {{ m.unit }}</span>
            </div>
            <div class="h-2 rounded-full bg-muted overflow-hidden">
              <div class="h-full rounded-full bg-primary" [style.width.%]="(m.after / m.before) * 100"></div>
            </div>
          </div>
        </div>
      }

      <!-- Optimization strategies card -->
      <div class="rounded-xl border bg-card p-6">
        <h4 class="font-semibold text-base mb-4">Optimization Strategies Applied</h4>
        <ul class="space-y-3">
          @for (s of strategies; track s.title; let i = $index) {
            <li class="flex items-start gap-3">
              <div class="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span class="text-xs font-bold text-primary">{{ i + 1 }}</span>
              </div>
              <div>
                <p class="font-medium">{{ s.title }}</p>
                <p class="text-sm text-muted-foreground">{{ s.desc }}</p>
              </div>
            </li>
          }
        </ul>
      </div>
    </div>
  `,
})
export class LiveComparisonSectionComponent {
  project = input.required<Project>();

  readonly metrics: Metric[] = [
    { label: 'API Response Time',       before: 450,  after: 180,  unit: 'ms',     improvement: 60 },
    { label: 'Token Usage per Request', before: 2500, after: 850,  unit: 'tokens', improvement: 66 },
    { label: 'Monthly API Cost',        before: 3200, after: 1150, unit: '$',      improvement: 64 },
    { label: 'Cache Hit Rate',          before: 45,   after: 87,   unit: '%',      improvement: 93 },
  ];

  readonly strategies: Strategy[] = [
    { title: 'Prompt Caching',           desc: 'Cached common prompt patterns to reduce redundant token processing' },
    { title: 'Response Compression',     desc: 'Optimized response formats to minimize token output without losing information' },
    { title: 'Smart Context Management', desc: 'Reduced context window size by intelligently selecting relevant information' },
    { title: 'Batch Processing',         desc: 'Grouped related queries to reduce API call overhead' },
  ];

  get tokenMetric(): Metric { return this.metrics.find(m => m.label === 'Token Usage per Request')!; }
  get costMetric(): Metric  { return this.metrics.find(m => m.label === 'Monthly API Cost')!; }
  get costSaving(): string  { return (this.costMetric.before - this.costMetric.after).toLocaleString(); }
}
