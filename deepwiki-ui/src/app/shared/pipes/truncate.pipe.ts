import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'truncate', standalone: true })
export class TruncatePipe implements PipeTransform {
  transform(value: string, limit = 80, trail = '...'): string {
    if (!value) return '';
    return value.length <= limit ? value : value.slice(0, limit) + trail;
  }
}
