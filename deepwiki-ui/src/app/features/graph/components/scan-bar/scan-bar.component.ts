import { Component, input } from '@angular/core';

@Component({
  selector: 'dw-scan-bar',
  standalone: true,
  template: `
    <footer style="border-top:1px solid #0D3464;padding:4px 24px;height:32px;background:#020C18"
            class="flex items-center text-xs shrink-0">
      <span style="color:#507898">
        {{ suiteCount() }} suite{{ suiteCount() !== 1 ? 's' : '' }}
        &nbsp;&#183;&nbsp;
        {{ projectCount() }} project{{ projectCount() !== 1 ? 's' : '' }}
        &nbsp;&#183;&nbsp;
        Click a node to explore
      </span>
    </footer>
  `,
})
export class ScanBarComponent {
  suiteCount   = input<number>(0);
  projectCount = input<number>(0);
}
