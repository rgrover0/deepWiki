import { Component, input, output } from '@angular/core';
import { GraphNode } from '../../../../core/models';

@Component({
  selector: 'dw-info-panel',
  standalone: true,
  template: `
    <div style="position:absolute;top:20px;right:20px;width:280px;background:#030E1C;
                border:1px solid #0D3464;border-radius:8px;padding:16px"
         class="text-sm">
      <div class="flex justify-between items-start mb-3">
        <h3 style="color:#B0D4EE;font-weight:bold">{{ node().label }}</h3>
        <button (click)="close.emit()"
          style="color:#507898;background:none;border:none;cursor:pointer;font-family:inherit">
          &#x2715;
        </button>
      </div>
      <p style="color:#507898;font-size:0.78rem">Type: {{ node().type }}</p>
      @if (node().type === 'project' || node().type === 'suite-center') {
        <button (click)="drill.emit(node())"
          style="margin-top:12px;padding:6px 14px;background:#2878CC;color:#fff;
                 border:none;border-radius:4px;cursor:pointer;font-family:inherit;font-size:0.8rem">
          Drill into {{ node().type === 'suite-center' ? 'suite' : 'project' }}
        </button>
      }
    </div>
  `,
})
export class InfoPanelComponent {
  node  = input.required<GraphNode>();
  close = output<void>();
  drill = output<GraphNode>();
}
