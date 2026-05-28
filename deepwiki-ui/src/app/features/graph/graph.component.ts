import {
  AfterViewInit, Component, ElementRef, NgZone, OnDestroy, OnInit,
  ViewChild, computed, inject, signal,
} from '@angular/core';
import * as d3 from 'd3';
import { ProjectService } from '../../core/services/project.service';
import { GraphDataService } from '../../core/services/graph-data.service';
import { D3RendererService } from '../../core/services/d3-renderer.service';
import { Suite, GraphNode, GraphLevel, GraphData } from '../../core/models';

@Component({
  selector: 'dw-graph',
  standalone: true,
  template: `
    <div class="graph-mode flex flex-col h-screen overflow-hidden"
         style="background:#020C18; font-family:'Courier New',monospace; color:#B0D4EE">

      <!-- Header -->
      <header style="border-bottom:1px solid #0D3464; padding:0 24px; height:56px"
              class="flex items-center justify-between shrink-0">
        <div class="flex items-center gap-3">
          <span style="color:#FFD100; font-weight:bold; font-size:1.1rem">&#9670; DeepWiki</span>
          <span style="color:#507898; font-size:0.85rem">Architecture Graph</span>
        </div>
        <div class="flex items-center gap-4 text-xs" style="color:#507898">
          <span>Level: <span style="color:#B0D4EE">{{ level() }}</span></span>
          @if (breadcrumb().length > 0) {
            <button (click)="drillUp()"
              style="color:#2878CC; cursor:pointer; background:none; border:none; font-family:inherit">
              &#8593; Back
            </button>
          }
        </div>
      </header>

      <!-- Graph canvas -->
      <div class="flex-1 relative overflow-hidden" #container>
        <svg #graphSvg class="w-full h-full"></svg>

        <!-- Info panel -->
        @if (selected()) {
          <div style="position:absolute;top:20px;right:20px;width:280px;background:#030E1C;
                      border:1px solid #0D3464;border-radius:8px;padding:16px"
               class="text-sm">
            <div class="flex justify-between items-start mb-3">
              <h3 style="color:#B0D4EE;font-weight:bold">{{ selected()!.label }}</h3>
              <button (click)="selected.set(null)"
                style="color:#507898;background:none;border:none;cursor:pointer;font-family:inherit">
                &#x2715;
              </button>
            </div>
            <p style="color:#507898;font-size:0.78rem">Type: {{ selected()!.type }}</p>
            @if (selected()!.type === 'suite-center' || selected()!.type === 'project') {
              <button (click)="drillInto(selected()!)"
                style="margin-top:12px;padding:6px 14px;background:#2878CC;color:#fff;
                       border:none;border-radius:4px;cursor:pointer;font-family:inherit;font-size:0.8rem">
                Drill into {{ selected()!.type === 'suite-center' ? 'suite' : 'project' }}
              </button>
            }
            @if (selected()!.type === 'project-center') {
              <p style="margin-top:10px;color:#7aa4c6;font-size:0.78rem">
                This view shows module-level architecture. Select module nodes for details.
              </p>
            }
            @if (selected()!.type === 'module') {
              <p style="margin-top:10px;color:#7aa4c6;font-size:0.78rem">
                Module node selected. Use Back to return to project or suite level.
              </p>
            }
          </div>
        }

        <!-- Legend -->
        <div style="position:absolute;bottom:20px;left:20px;background:#030E1C;
                    border:1px solid #0D3464;border-radius:8px;padding:12px" class="text-xs">
          <p style="color:#507898;margin-bottom:6px">LEGEND</p>
          @for (item of legendItems; track item.label) {
            <div class="flex items-center gap-2 mb-1">
              <span style="width:10px;height:10px;border-radius:50%;display:inline-block"
                    [style.background]="item.color"></span>
              <span style="color:#B0D4EE">{{ item.label }}</span>
            </div>
          }
        </div>
      </div>

      <!-- Status bar -->
      <footer style="border-top:1px solid #0D3464;padding:4px 24px;height:32px;background:#020C18"
              class="flex items-center text-xs shrink-0" style-add="color:#507898">
        <span style="color:#507898">
          {{ suites().length }} suite{{ suites().length !== 1 ? 's' : '' }}
          &nbsp;·&nbsp; {{ totalProjects() }} project{{ totalProjects() !== 1 ? 's' : '' }}
          &nbsp;·&nbsp; Click a node to explore
        </span>
      </footer>
    </div>
  `,
})
export class GraphComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('container') container!: ElementRef<HTMLDivElement>;
  @ViewChild('graphSvg')  svgEl!: ElementRef<SVGSVGElement>;

  private projectService   = inject(ProjectService);
  private graphDataService = inject(GraphDataService);
  private renderer         = inject(D3RendererService);
  private ngZone           = inject(NgZone);

  suites        = signal<Suite[]>([]);
  level         = signal<GraphLevel>('cosmos');
  breadcrumb    = signal<string[]>([]);
  selected      = signal<GraphNode | null>(null);
  totalProjects = computed(() => this.suites().reduce((n, s) => n + s.projects.length, 0));

  private simulation: d3.Simulation<any, any> | null = null;

  legendItems = [
    { color: '#2878CC', label: 'Suite'   },
    { color: '#1D9E75', label: 'Project' },
    { color: '#8870DD', label: 'Module'  },
  ];

  graphData = computed((): GraphData => {
    const s = this.suites();
    if (!s.length) return { nodes: [], links: [] };
    const W = typeof window !== 'undefined' ? window.innerWidth  : 1200;
    const H = typeof window !== 'undefined' ? window.innerHeight - 100 : 700;
    if (this.level() === 'cosmos') return this.graphDataService.buildCosmosGraph(s, W, H);
    if (this.level() === 'suite')  return this.graphDataService.buildSuiteGraph(this.breadcrumb()[0], s, W, H);
    return this.graphDataService.buildProjectGraph(this.breadcrumb()[1], s, W, H);
  });

  ngOnInit() {
    this.projectService.getSuites().subscribe(s => this.suites.set(s));
  }

  ngAfterViewInit() {
    // Re-render whenever suites load
    setTimeout(() => this.render(), 100);
  }

  private render() {
    if (!this.svgEl || !this.container) return;
    const { clientWidth: W, clientHeight: H } = this.container.nativeElement;
    if (!W || !H) return;
    this.simulation = this.renderer.render(
      this.svgEl.nativeElement,
      this.graphData(),
      W, H,
      node => this.ngZone.run(() => {
        this.selected.set(node);
        if (node.type === 'suite-center' || node.type === 'project') {
          this.drillInto(node);
        }
      })
    );
  }

  drillInto(node: GraphNode) {
    if (node.type === 'suite-center') {
      this.level.set('suite');
      this.breadcrumb.set([node.id.replace('suite-', '')]);
    } else if (node.type === 'project') {
      this.level.set('project');
      this.breadcrumb.update(b => [...b, node.id.replace('project-', '')]);
    }
    this.selected.set(null);
    setTimeout(() => this.render(), 50);
  }

  drillUp() {
    const b = this.breadcrumb();
    if (b.length >= 2) {
      this.level.set('suite');
      this.breadcrumb.set([b[0]]);
    } else {
      this.level.set('cosmos');
      this.breadcrumb.set([]);
    }
    this.selected.set(null);
    setTimeout(() => this.render(), 50);
  }

  ngOnDestroy() { this.renderer.destroy(this.simulation); }
}
