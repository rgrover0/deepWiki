import { Component, InjectionToken, computed, effect, inject, input, output, signal } from '@angular/core';

const TABS_CTX = new InjectionToken<TabsComponent>('TabsCtx');

@Component({
  selector: 'dw-tabs',
  standalone: true,
  template: `<ng-content />`,
  host: { class: 'block' },
  providers: [{ provide: TABS_CTX, useExisting: TabsComponent }],
})
export class TabsComponent {
  value       = input<string>('');
  valueChange = output<string>();

  activeTab = signal<string>('');

  constructor() {
    effect(() => {
      const v = this.value();
      if (v && !this.activeTab()) this.activeTab.set(v);
    }, { allowSignalWrites: true });
  }

  select(tab: string) {
    this.activeTab.set(tab);
    this.valueChange.emit(tab);
  }

  isActive(tab: string): boolean {
    return this.activeTab() === tab;
  }
}

@Component({
  selector: 'dw-tabs-list',
  standalone: true,
  template: `
    <div class="inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground">
      <ng-content />
    </div>
  `,
})
export class TabsListComponent {}

@Component({
  selector: 'dw-tabs-trigger',
  standalone: true,
  template: `<ng-content />`,
  host: {
    class: 'inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium transition-all cursor-pointer disabled:pointer-events-none disabled:opacity-50',
    '[class.bg-background]': 'active()',
    '[class.text-foreground]': 'active()',
    '[class.shadow-sm]': 'active()',
    '[class.text-muted-foreground]': '!active()',
    '[class.hover:text-foreground]': '!active()',
    '(click)': 'activate()',
  },
})
export class TabsTriggerComponent {
  value   = input.required<string>();
  private tabs = inject(TABS_CTX, { optional: true }) as TabsComponent | null;

  active = computed(() => this.tabs?.isActive(this.value()) ?? false);

  activate() { this.tabs?.select(this.value()); }
}

@Component({
  selector: 'dw-tabs-content',
  standalone: true,
  template: `@if (visible()) { <div class="mt-4"><ng-content /></div> }`,
})
export class TabsContentComponent {
  value   = input.required<string>();
  private tabs = inject(TABS_CTX, { optional: true }) as TabsComponent | null;

  visible = computed(() => this.tabs?.isActive(this.value()) ?? true);
}
