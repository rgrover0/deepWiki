import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { Router } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';

@Component({
  selector: 'dw-header',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, LucideAngularModule],
  template: `
    <header class="sticky top-0 z-50 w-full border-b bg-primary text-primary-foreground">
      <div class="container mx-auto flex h-16 items-center px-4">

        <a routerLink="/" class="flex items-center space-x-2">
          <lucide-icon name="layers" class="h-6 w-6 text-penske-yellow" />
          <span class="font-bold text-xl">DeepWiki</span>
        </a>

        <nav class="ml-10 flex gap-6">
          <a routerLink="/" routerLinkActive="text-penske-yellow" [routerLinkActiveOptions]="{exact:true}"
             class="text-sm font-medium flex items-center gap-2 hover:text-penske-yellow transition-colors">
            <lucide-icon name="layers" class="h-4 w-4" /> All Projects
          </a>
          <a routerLink="/search" routerLinkActive="text-penske-yellow"
             class="text-sm font-medium flex items-center gap-2 hover:text-penske-yellow transition-colors">
            <lucide-icon name="search" class="h-4 w-4" /> Search
          </a>
          <a routerLink="/graph" routerLinkActive="text-penske-yellow"
             class="text-sm font-medium flex items-center gap-2 hover:text-penske-yellow transition-colors">
            <lucide-icon name="share-2" class="h-4 w-4" /> Architecture
          </a>
          <a routerLink="/admin" routerLinkActive="text-penske-yellow"
             class="text-sm font-medium flex items-center gap-2 hover:text-penske-yellow transition-colors">
            <lucide-icon name="settings" class="h-4 w-4" /> Admin
          </a>
        </nav>

        <div class="ml-auto relative w-64">
          <lucide-icon name="search"
            class="absolute left-2.5 top-2.5 h-4 w-4 text-primary-foreground/60 pointer-events-none" />
          <input
            type="search"
            placeholder="Quick search..."
            #qs
            (keyup.enter)="onSearch(qs.value)"
            class="pl-8 w-full h-10 rounded-md bg-primary-foreground/10 border border-primary-foreground/20
                   text-primary-foreground placeholder:text-primary-foreground/60 text-sm px-3 py-2
                   focus:outline-none focus:ring-2 focus:ring-penske-yellow"
          />
        </div>

      </div>
    </header>
  `,
})
export class HeaderComponent {
  private router = inject(Router);
  onSearch(q: string) {
    if (q.trim()) this.router.navigate(['/search'], { queryParams: { q } });
  }
}
