import { Component, computed, inject, input, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { WikiService } from '../../../../core/services/wiki.service';
import { Project } from '../../../../core/models';

@Component({
  selector: 'dw-live-comparison-section',
  standalone: true,
  imports: [DecimalPipe],
  template: `
    <div class="max-w-2xl space-y-4">
      <div>
        <h2 class="text-lg font-semibold">Live Token Comparison</h2>
        <p class="text-sm text-muted-foreground mt-1">
          Compare DeepWiki token usage vs raw source retrieval on the same query.
        </p>
      </div>
      <div class="flex gap-2">
        <input #cq type="text" placeholder="How does owner creation work?"
          (keyup.enter)="runComparison(cq.value)"
          class="flex-1 h-10 rounded-[0.625rem] border px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
        <button (click)="runComparison(cq.value)"
          [disabled]="loading()"
          class="h-10 px-4 rounded-[0.625rem] bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50">
          Compare
        </button>
      </div>
      @if (loading()) {
        <div class="space-y-2 animate-pulse">
          @for (_ of [1,2]; track $index) {
            <div class="h-16 rounded bg-muted"></div>
          }
        </div>
      }
      @if (result()) {
        <div class="grid grid-cols-2 gap-4">
          <div class="rounded-[0.625rem] border p-4">
            <h3 class="font-semibold text-sm mb-2">With DeepWiki</h3>
            <p class="text-2xl font-bold text-green-600">{{ result()?.wiki?.total_tokens ?? 0 | number }}</p>
            <p class="text-xs text-muted-foreground">tokens</p>
          </div>
          <div class="rounded-[0.625rem] border p-4">
            <h3 class="font-semibold text-sm mb-2">Without (Raw)</h3>
            <p class="text-2xl font-bold text-destructive">{{ result()?.raw?.total_tokens ?? 0 | number }}</p>
            <p class="text-xs text-muted-foreground">tokens</p>
          </div>
          @if (savings() > 0) {
            <div class="col-span-2 rounded-[0.625rem] border p-4 bg-green-50">
              <p class="text-sm font-medium text-green-800">
                {{ savings() }}% fewer tokens with DeepWiki
              </p>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class LiveComparisonSectionComponent {
  project = input.required<Project>();

  private wikiService = inject(WikiService);

  loading = signal(false);
  result  = signal<any>(null);

  savings = computed(() => {
    const r = this.result();
    if (!r?.wiki?.total_tokens || !r?.raw?.total_tokens) return 0;
    return Math.round((1 - r.wiki.total_tokens / r.raw.total_tokens) * 100);
  });

  runComparison(query: string) {
    if (!query.trim()) return;
    this.loading.set(true);
    this.result.set(null);
    this.wikiService.compare(query).subscribe({
      next: res => { this.result.set(res); this.loading.set(false); },
      error: ()  => this.loading.set(false),
    });
  }
}
