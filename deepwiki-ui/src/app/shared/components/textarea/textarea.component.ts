import { Component, forwardRef, input } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

@Component({
  selector: 'dw-textarea',
  standalone: true,
  template: `
    <textarea
      [placeholder]="placeholder()"
      [rows]="rows()"
      [disabled]="disabled"
      (input)="onInput($event)"
      (blur)="onTouched()"
      [value]="value"
      class="flex w-full rounded-[0.625rem] border border-input bg-background px-3 py-2 text-sm
             placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring
             disabled:cursor-not-allowed disabled:opacity-50 resize-none"
    ></textarea>
  `,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => TextareaComponent),
    multi: true,
  }],
})
export class TextareaComponent implements ControlValueAccessor {
  placeholder = input('');
  rows        = input(3);

  value    = '';
  disabled = false;

  private onChange   = (_: string) => {};
  onTouched = () => {};

  writeValue(v: string)    { this.value = v ?? ''; }
  registerOnChange(fn: any)  { this.onChange = fn; }
  registerOnTouched(fn: any) { this.onTouched = fn; }
  setDisabledState(d: boolean) { this.disabled = d; }

  onInput(e: Event) {
    const v = (e.target as HTMLTextAreaElement).value;
    this.value = v;
    this.onChange(v);
  }
}
