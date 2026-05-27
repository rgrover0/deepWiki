import { Component } from '@angular/core';

@Component({
  selector: 'dw-footer',
  standalone: true,
  template: `
    <footer class="border-t py-6 text-center text-sm text-muted-foreground">
      DeepWiki &mdash; Codebase Intelligence Platform
    </footer>
  `,
})
export class FooterComponent {}
