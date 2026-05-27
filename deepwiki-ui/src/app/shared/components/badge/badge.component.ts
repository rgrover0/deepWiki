import { Component, computed, input } from '@angular/core';

@Component({
  selector: 'dw-badge',
  standalone: true,
  template: `<span [class]="classes()"><ng-content /></span>`,
})
export class BadgeComponent {
  variant = input<'default' | 'secondary' | 'outline' | 'destructive'>('default');

  classes = computed(() => {
    const base = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors';
    const map: Record<string, string> = {
      default:     'bg-primary text-primary-foreground',
      secondary:   'bg-secondary text-secondary-foreground',
      outline:     'border border-[rgba(0,0,0,0.1)] text-foreground',
      destructive: 'bg-destructive text-destructive-foreground',
    };
    return `${base} ${map[this.variant()]}`;
  });
}
