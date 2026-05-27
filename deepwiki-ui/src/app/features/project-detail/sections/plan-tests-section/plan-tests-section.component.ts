import { Component, inject, input, signal } from '@angular/core';
import { WikiService } from '../../../../core/services/wiki.service';
import { Project } from '../../../../core/models';

@Component({
  selector: 'dw-plan-tests-section',
  standalone: true,
  template: `
    <div class="max-w-2xl space-y-4">
      <div>
        <h2 class="text-lg font-semibold">Plan & Tests</h2>
        <p class="text-sm text-muted-foreground mt-1">
          Describe a requirement to generate an implementation plan.
        </p>
      </div>
      <div class="flex gap-2">
        <input #ri type="text" placeholder="Add phone validation to owner creation..."
          (keyup.enter)="generatePlan(ri.value)"
          class="flex-1 h-10 rounded-[0.625rem] border px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
        <button (click)="generatePlan(ri.value)"
          [disabled]="loading()"
          class="h-10 px-4 rounded-[0.625rem] bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50">
          Generate
        </button>
      </div>
      @if (loading()) {
        <div class="space-y-2 animate-pulse">
          @for (_ of [1,2,3,4]; track $index) {
            <div class="h-3 rounded bg-muted" [style.width]="$index % 2 === 0 ? '100%' : '80%'"></div>
          }
        </div>
      }
      @if (planResult()) {
        <div class="rounded-[0.625rem] border p-4">
          <pre class="whitespace-pre-wrap text-sm font-mono">{{ planResult() }}</pre>
        </div>
      }
    </div>
  `,
})
export class PlanTestsSectionComponent {
  project = input.required<Project>();

  private wikiService = inject(WikiService);

  loading    = signal(false);
  planResult = signal<string | null>(null);

  generatePlan(req: string) {
    if (!req.trim()) return;
    this.loading.set(true);
    this.planResult.set(null);
    this.wikiService.generatePlan(req, this.project().id).subscribe({
      next: res => { this.planResult.set(res.plan); this.loading.set(false); },
      error: ()  => this.loading.set(false),
    });
  }
}
