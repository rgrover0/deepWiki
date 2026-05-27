import {
  AfterViewInit, Component, ElementRef, NgZone,
  OnChanges, OnDestroy, SimpleChanges, ViewChild,
  inject, input, output,
} from '@angular/core';
import * as d3 from 'd3';
import { D3RendererService } from '../../../../core/services/d3-renderer.service';
import { GraphData, GraphNode } from '../../../../core/models';

@Component({
  selector: 'dw-force-graph',
  standalone: true,
  template: `
    <div #container class="w-full h-full relative overflow-hidden">
      <svg #graphSvg class="w-full h-full"></svg>
    </div>
  `,
  host: { class: 'block w-full h-full' },
})
export class ForceGraphComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('container') container!: ElementRef<HTMLDivElement>;
  @ViewChild('graphSvg')  svgEl!: ElementRef<SVGSVGElement>;

  graphData  = input.required<GraphData>();
  nodeClick  = output<GraphNode>();

  private renderer   = inject(D3RendererService);
  private ngZone     = inject(NgZone);
  private simulation: d3.Simulation<any, any> | null = null;

  ngAfterViewInit() { this.render(); }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['graphData'] && !changes['graphData'].firstChange) {
      this.render();
    }
  }

  render() {
    if (!this.svgEl || !this.container) return;
    const { clientWidth: W, clientHeight: H } = this.container.nativeElement;
    if (!W || !H) return;
    this.simulation?.stop();
    this.simulation = this.renderer.render(
      this.svgEl.nativeElement,
      this.graphData(),
      W, H,
      node => this.ngZone.run(() => this.nodeClick.emit(node)),
    );
  }

  ngOnDestroy() { this.renderer.destroy(this.simulation); }
}
