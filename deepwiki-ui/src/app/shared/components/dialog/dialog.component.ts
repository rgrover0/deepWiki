import { Component, input, output } from '@angular/core';

@Component({
  selector: 'dw-dialog',
  standalone: true,
  template: `
    @if (open()) {
      <!-- Backdrop -->
      <div class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/50" (click)="openChange.emit(false)"></div>

        <!-- Panel -->
        <div class="relative z-10 w-full max-w-lg rounded-[0.625rem] bg-background border shadow-lg p-6 mx-4">
          @if (title()) {
            <div class="flex items-start justify-between mb-4">
              <h2 class="text-lg font-semibold">{{ title() }}</h2>
              <button (click)="openChange.emit(false)"
                class="text-muted-foreground hover:text-foreground transition-colors ml-4 shrink-0">
                &#x2715;
              </button>
            </div>
          }
          <ng-content />
        </div>
      </div>
    }
  `,
})
export class DialogComponent {
  open       = input<boolean>(false);
  title      = input<string>('');
  openChange = output<boolean>();
}
