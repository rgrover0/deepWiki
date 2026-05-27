import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HeaderComponent } from '../header/header.component';
import { FooterComponent } from '../footer/footer.component';

@Component({
  selector: 'dw-app-shell',
  standalone: true,
  imports: [RouterOutlet, HeaderComponent, FooterComponent],
  template: `
    <dw-header />
    <main class="min-h-[calc(100vh-8rem)]">
      <router-outlet />
    </main>
    <dw-footer />
  `,
})
export class AppShellComponent {}
