import { Component } from '@angular/core';

@Component({
  selector: 'dw-card',
  standalone: true,
  template: `<div class="rounded-[0.625rem] border border-[rgba(0,0,0,0.1)] bg-background shadow-sm"><ng-content /></div>`,
})
export class CardComponent {}

@Component({
  selector: 'dw-card-header',
  standalone: true,
  template: `<div class="flex flex-col space-y-1.5 p-6"><ng-content /></div>`,
})
export class CardHeaderComponent {}

@Component({
  selector: 'dw-card-title',
  standalone: true,
  template: `<h3 class="text-lg font-semibold leading-none tracking-tight"><ng-content /></h3>`,
})
export class CardTitleComponent {}

@Component({
  selector: 'dw-card-description',
  standalone: true,
  template: `<p class="text-sm text-muted-foreground"><ng-content /></p>`,
})
export class CardDescriptionComponent {}

@Component({
  selector: 'dw-card-content',
  standalone: true,
  template: `<div class="p-6 pt-0"><ng-content /></div>`,
})
export class CardContentComponent {}
