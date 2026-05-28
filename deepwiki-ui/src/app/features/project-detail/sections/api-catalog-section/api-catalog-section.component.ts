import { Component, computed, input, signal } from '@angular/core';
import { Project } from '../../../../core/models';
import { LucideAngularModule } from 'lucide-angular';

@Component({
  selector: 'dw-api-catalog-section',
  standalone: true,
  imports: [LucideAngularModule],
  template: `
    <div class="space-y-6">

      <!-- Header card with search + stat cards -->
      <div class="rounded-xl border bg-card p-6 space-y-4">
        <div class="flex items-center gap-2">
          <lucide-icon name="git-branch" class="h-5 w-5 text-primary"></lucide-icon>
          <h3 class="font-semibold text-lg">API Catalog</h3>
        </div>
        <p class="text-sm text-muted-foreground">
          Browse all APIs exposed and consumed by {{ project().name }}
        </p>

        <div class="relative">
          <lucide-icon name="search"
            class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none">
          </lucide-icon>
          <input
            type="text"
            [value]="query()"
            (input)="query.set(asStr($event))"
            placeholder="Search APIs by name, endpoint, or description..."
            class="w-full pl-8 h-10 rounded-lg border px-3 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div class="grid gap-4 md:grid-cols-3">
          <div class="rounded-lg border p-4 bg-primary/5 space-y-1">
            <p class="text-sm font-medium">Total APIs</p>
            <p class="text-2xl font-bold">{{ project().apis.length }}</p>
          </div>
          <div class="rounded-lg border p-4 bg-green-50 space-y-1">
            <p class="text-sm font-medium flex items-center gap-2">
              <lucide-icon name="arrow-up-from-line" class="h-4 w-4"></lucide-icon>
              Exposed
            </p>
            <p class="text-2xl font-bold">{{ exposed().length }}</p>
          </div>
          <div class="rounded-lg border p-4 bg-blue-50 space-y-1">
            <p class="text-sm font-medium flex items-center gap-2">
              <lucide-icon name="arrow-down-to-line" class="h-4 w-4"></lucide-icon>
              Consumed
            </p>
            <p class="text-2xl font-bold">{{ consumed().length }}</p>
          </div>
        </div>
      </div>

      <!-- Tab bar -->
      <div class="border-b flex">
        <button (click)="tab.set('all')" [class]="tabClass(tab() === 'all')">
          All APIs ({{ project().apis.length }})
        </button>
        <button (click)="tab.set('exposed')" [class]="tabClass(tab() === 'exposed')">
          Exposed ({{ exposed().length }})
        </button>
        <button (click)="tab.set('consumed')" [class]="tabClass(tab() === 'consumed')">
          Consumed ({{ consumed().length }})
        </button>
      </div>

      <!-- API cards -->
      <div class="space-y-4">
        @for (api of list(); track api.id) {
          <div class="rounded-xl border bg-card p-6 space-y-4">
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-2">
                  <span [class]="methodClass(api.method)">{{ api.method }}</span>
                  <h4 class="font-semibold">{{ api.name }}</h4>
                </div>
                <code class="text-sm bg-muted px-2 py-1 rounded">{{ api.endpoint }}</code>
              </div>
              <button class="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border hover:bg-muted transition-colors flex-shrink-0">
                <lucide-icon name="code" class="h-4 w-4"></lucide-icon>
                View Docs
              </button>
            </div>
            <p class="text-sm text-muted-foreground">{{ api.description }}</p>
            <div>
              @if (api.type === 'exposed') {
                <span class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border">
                  <lucide-icon name="arrow-up-from-line" class="h-3 w-3"></lucide-icon>
                  Exposed API
                </span>
              } @else {
                <span class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border">
                  <lucide-icon name="arrow-down-to-line" class="h-3 w-3"></lucide-icon>
                  Consumed API
                </span>
              }
            </div>
          </div>
        } @empty {
          <p class="text-center py-8 text-muted-foreground">
            @if (query()) {
              No APIs found matching "{{ query() }}"
            } @else {
              No APIs found
            }
          </p>
        }
      </div>
    </div>
  `,
})
export class ApiCatalogSectionComponent {
  project = input.required<Project>();

  query = signal('');
  tab   = signal<'all' | 'exposed' | 'consumed'>('all');

  exposed  = computed(() => this.project().apis.filter(a => a.type === 'exposed'));
  consumed = computed(() => this.project().apis.filter(a => a.type === 'consumed'));

  list = computed(() => {
    const q = this.query().toLowerCase();
    const base = this.tab() === 'exposed'  ? this.exposed()
               : this.tab() === 'consumed' ? this.consumed()
               : this.project().apis;
    if (!q) return base;
    return base.filter(a =>
      a.name.toLowerCase().includes(q) ||
      a.endpoint.toLowerCase().includes(q) ||
      a.description.toLowerCase().includes(q)
    );
  });

  tabClass(active: boolean) {
    const base = 'px-4 py-2 text-sm font-medium -mb-px border-b-2 transition-colors';
    return active
      ? `${base} border-primary text-primary`
      : `${base} border-transparent text-muted-foreground hover:text-foreground`;
  }

  methodClass(method: string) {
    const base = 'text-xs font-bold px-2 py-1 rounded min-w-[52px] text-center';
    const map: Record<string, string> = {
      GET:    'bg-blue-100 text-blue-700',
      POST:   'bg-green-100 text-green-700',
      PUT:    'bg-yellow-100 text-yellow-700',
      DELETE: 'bg-red-100 text-red-700',
      PATCH:  'bg-purple-100 text-purple-700',
    };
    return `${base} ${map[method.toUpperCase()] ?? 'bg-gray-100 text-gray-700'}`;
  }

  asStr(e: Event): string {
    return (e.target as HTMLInputElement).value;
  }
}
