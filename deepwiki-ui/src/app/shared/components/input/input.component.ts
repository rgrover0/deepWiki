import { Component, forwardRef, input } from '@angular/core';
import { NG_VALUE_ACCESSOR, ControlValueAccessor, FormsModule } from '@angular/forms';

@Component({
  selector: 'dw-input',
  standalone: true,
  imports: [FormsModule],
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => InputComponent),
    multi: true,
  }],
  template: `
    <input
      [type]="type()"
      [placeholder]="placeholder()"
      [(ngModel)]="value"
      (ngModelChange)="onChange($event)"
      (blur)="onTouched()"
      class="flex h-10 w-full rounded-[0.625rem] border border-[rgba(0,0,0,0.1)] bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
    />
  `,
})
export class InputComponent implements ControlValueAccessor {
  type        = input<string>('text');
  placeholder = input<string>('');
  value       = '';

  onChange  = (_: any) => {};
  onTouched = () => {};

  writeValue(val: string)         { this.value = val ?? ''; }
  registerOnChange(fn: any)       { this.onChange = fn; }
  registerOnTouched(fn: any)      { this.onTouched = fn; }
}
