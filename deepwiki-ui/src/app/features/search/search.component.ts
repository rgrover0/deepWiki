import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { DecimalPipe } from '@angular/common';
import { Title } from '@angular/platform-browser';
import { WikiService } from '../../core/services/wiki.service';
import { SearchResult } from '../../core/models';
import { ProgressComponent } from '../../shared/components/progress/progress.component';

@Component({
  selector: 'dw-search',
  standalone: true,
  imports: [ProgressComponent, DecimalPipe],
  template: `
    <div class="container mx-auto px-4 py-10 space-y-6">
      <div class="space-y-1">
        <h1 class="text-3xl font-bold">Search</h1>
        <p class="text-muted-foreground">Find classes and methods by meaning, not just keywords.</p>
      </div>

      <!-- Search bar -->
      <div class="flex gap-3">
        <input
          [value]="query()"
          (input)="query.set(asStr($event))"
          (keyup.enter)="search()"
          type="text"
          placeholder="Find methods that validate email..."
          class="flex-1 h-10 rounded-[0.625rem] border px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <select
          [value]="unitType()"
          (change)="unitType.set(asStr($event))"
          class="h-10 rounded-[0.625rem] border px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-background">
          <option value="">Classes + Methods</option>
          <option value="class">Classes only</option>
          <option value="method">Methods only</option>
        </select>
        <button (click)="search()" [disabled]="loading()"
          class="h-10 px-5 rounded-[0.625rem] bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50">
          Search
        </button>
      </div>

      <!-- Tech filter chips -->
      @if (activeTechs().size > 0 || techOptions().length > 0) {
        <div class="flex flex-wrap gap-2 items-center">
          <span class="text-xs text-muted-foreground mr-1">Filter:</span>
          @for (tech of techOptions(); track tech) {
            <button
              (click)="toggleTech(tech)"
              [class]="techChipClass(tech)">
              {{ tech }}
            </button>
          }
          @if (activeTechs().size > 0) {
            <button (click)="clearTechs()"
              class="text-xs text-muted-foreground underline">
              Clear
            </button>
          }
        </div>
      }

      <!-- Loading -->
      @if (loading()) {
        <div class="space-y-3">
          @for (_ of skeletons; track $index) {
            <div class="rounded-[0.625rem] border p-4 animate-pulse">
              <div class="flex justify-between items-center">
                <div class="h-4 w-48 rounded bg-muted"></div>
                <div class="h-3 w-24 rounded bg-muted"></div>
              </div>
              <div class="h-3 w-3/4 rounded bg-muted mt-2"></div>
            </div>
          }
        </div>
      }

      <!-- Results -->
      @if (!loading() && filteredResults().length > 0) {
        <p class="text-sm text-muted-foreground">
          {{ filteredResults().length }} of {{ results().length }} results
        </p>
        <div class="space-y-3">
          @for (r of filteredResults(); track r.name) {
            <div class="rounded-[0.625rem] border p-4 hover:shadow-sm transition-shadow">
              <div class="flex items-center justify-between mb-1">
                <div>
                  @if (r.unit_type === 'method') {
                    <span class="font-mono text-sm font-semibold">
                      {{ r.class_name }}.{{ r.name }}()
                    </span>
                    <span class="ml-2 text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground">method</span>
                  } @else {
                    <span class="font-semibold">{{ r.name }}</span>
                    <span class="ml-2 text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground">
                      {{ r.component_type }}
                    </span>
                  }
                </div>
                <div class="flex items-center gap-2 w-32">
                  <dw-progress [value]="r.score * 100" />
                  <span class="text-xs text-muted-foreground w-10 text-right">
                    {{ (r.score * 100) | number:'1.0-0' }}%
                  </span>
                </div>
              </div>
              @if (r.logic_summary ?? r.wiki_summary) {
                <p class="text-sm text-muted-foreground">{{ r.logic_summary ?? r.wiki_summary }}</p>
              }
            </div>
          }
        </div>
      }

      <!-- Empty state -->
      @if (!loading() && searched() && results().length === 0) {
        <div class="text-center py-16 text-muted-foreground">
          <p class="text-lg">No results for "{{ lastQuery() }}"</p>
          <p class="text-sm mt-1">Try a different query or broaden the unit type filter.</p>
        </div>
      }

      <!-- Initial hint -->
      @if (!loading() && !searched()) {
        <div class="text-center py-16 text-muted-foreground">
          <p>Enter a query above to search the knowledge graph.</p>
        </div>
      }
    </div>
  `,
})
export class SearchComponent implements OnInit {
  private wikiService = inject(WikiService);
  private route       = inject(ActivatedRoute);
  private router      = inject(Router);
  private title       = inject(Title);

  query      = signal('');
  unitType   = signal('');
  results    = signal<SearchResult[]>([]);
  loading    = signal(false);
  searched   = signal(false);
  lastQuery  = signal('');
  activeTechs = signal(new Set<string>());
  skeletons   = new Array(5);

  techOptions     = signal<string[]>([]);
  filteredResults = computed(() => {
    const active = this.activeTechs();
    if (!active.size) return this.results();
    return this.results().filter(r => r.component_type && active.has(r.component_type));
  });

  ngOnInit() {
    this.title.setTitle('DeepWiki — Search');
    const q = this.route.snapshot.queryParamMap.get('q');
    if (q) { this.query.set(q); this.search(); }
  }

  search() {
    const q = this.query().trim();
    if (!q) return;
    this.loading.set(true);
    this.searched.set(true);
    this.lastQuery.set(q);
    this.router.navigate([], { queryParams: { q }, replaceUrl: true });

    this.wikiService.search(q, 20, this.unitType() || undefined).subscribe({
      next: res => {
        this.results.set(res.results);
        const types = [...new Set(res.results.map((r: SearchResult) => r.component_type).filter(Boolean))];
        this.techOptions.set(types as string[]);
        this.activeTechs.set(new Set());
        this.loading.set(false);
      },
      error: () => { this.results.set([]); this.loading.set(false); },
    });
  }

  clearTechs() { this.activeTechs.set(new Set()); }

  toggleTech(tech: string) {
    this.activeTechs.update(s => {
      const next = new Set(s);
      next.has(tech) ? next.delete(tech) : next.add(tech);
      return next;
    });
  }

  techChipClass(tech: string) {
    const base = 'text-xs px-2.5 py-1 rounded-full border transition-colors';
    return this.activeTechs().has(tech)
      ? `${base} bg-primary text-primary-foreground border-primary`
      : `${base} text-muted-foreground hover:text-foreground`;
  }

  asStr(e: Event): string {
    return (e.target as HTMLInputElement | HTMLSelectElement).value;
  }
}
