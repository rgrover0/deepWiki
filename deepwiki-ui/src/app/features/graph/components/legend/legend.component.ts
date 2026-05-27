import { Component } from '@angular/core';

@Component({
  selector: 'dw-legend',
  standalone: true,
  template: `
    <div style="position:absolute;bottom:20px;left:20px;background:#030E1C;
                border:1px solid #0D3464;border-radius:8px;padding:12px"
         class="text-xs">
      <p style="color:#507898;margin-bottom:6px">LEGEND</p>
      @for (item of items; track item.label) {
        <div class="flex items-center gap-2 mb-1">
          <span style="width:10px;height:10px;border-radius:50%;display:inline-block"
                [style.background]="item.color"></span>
          <span style="color:#B0D4EE">{{ item.label }}</span>
        </div>
      }
    </div>
  `,
})
export class LegendComponent {
  items = [
    { color: '#2878CC', label: 'Suite'   },
    { color: '#1D9E75', label: 'Project' },
    { color: '#8870DD', label: 'Module'  },
  ];
}
