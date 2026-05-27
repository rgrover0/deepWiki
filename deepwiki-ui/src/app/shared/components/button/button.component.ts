import { Component, computed, input } from '@angular/core';

@Component({
  selector: 'button[dw-button], a[dw-button]',
  standalone: true,
  template: `<ng-content />`,
  host: { '[class]': 'classes()' },
})
export class ButtonComponent {
  variant = input<'default' | 'outline' | 'ghost' | 'link'>('default');
  size    = input<'sm' | 'md' | 'lg'>('md');

  classes = computed(() => {
    const base = 'inline-flex items-center justify-center font-medium rounded-[0.625rem] transition-colors focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 cursor-pointer';
    const variants: Record<string, string> = {
      default: 'bg-primary text-primary-foreground hover:bg-primary/90',
      outline: 'border border-[rgba(0,0,0,0.1)] bg-background hover:bg-accent hover:text-foreground',
      ghost:   'hover:bg-accent hover:text-foreground',
      link:    'text-primary underline-offset-4 hover:underline',
    };
    const sizes: Record<string, string> = {
      sm: 'h-8 px-3 text-xs',
      md: 'h-10 px-4 py-2 text-sm',
      lg: 'h-12 px-6 text-base',
    };
    return `${base} ${variants[this.variant()]} ${sizes[this.size()]}`;
  });
}
