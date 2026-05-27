import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'methodColor', standalone: true })
export class MethodColorPipe implements PipeTransform {
  transform(method: string): string {
    const map: Record<string, string> = {
      'GET':    'bg-blue-100 text-blue-700',
      'POST':   'bg-green-100 text-green-700',
      'PUT':    'bg-yellow-100 text-yellow-700',
      'DELETE': 'bg-red-100 text-red-700',
      'PATCH':  'bg-purple-100 text-purple-700',
    };
    return map[method?.toUpperCase()] ?? 'bg-gray-100 text-gray-700';
  }
}
