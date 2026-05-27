import { Component, input } from '@angular/core';
import { MethodColorPipe } from '../../../../../shared/pipes/method-color.pipe';
import { ApiContract } from '../../../../../core/models';

@Component({
  selector: 'dw-api-card',
  standalone: true,
  imports: [MethodColorPipe],
  template: `
    <div class="flex items-center gap-3 rounded-[0.625rem] border p-3">
      <span [class]="'text-xs font-bold px-2 py-1 rounded min-w-[52px] text-center ' + (api().method | methodColor)">
        {{ api().method }}
      </span>
      <code class="text-sm font-mono flex-1 truncate">{{ api().endpoint }}</code>
      <span class="text-xs text-muted-foreground hidden sm:block">{{ api().description }}</span>
    </div>
  `,
})
export class ApiCardComponent {
  api = input.required<ApiContract>();
}
