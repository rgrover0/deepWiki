import { Component, computed, input } from '@angular/core';

@Component({
  selector: 'dw-progress',
  standalone: true,
  template: `
    <div class="relative h-2 w-full overflow-hidden rounded-full bg-secondary">
      <div
        class="h-full bg-primary transition-all"
        [style.width.%]="clamped()"
      ></div>
    </div>
  `,
})
export class ProgressComponent {
  value   = input<number>(0);
  clamped = computed(() => Math.min(100, Math.max(0, this.value())));
}
