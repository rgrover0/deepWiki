import { Injectable, NgZone, inject } from '@angular/core';
import * as d3 from 'd3';
import { GraphData, GraphNode, GraphLink } from '../models';

@Injectable({ providedIn: 'root' })
export class D3RendererService {
  private ngZone = inject(NgZone);

  render(
    svgElement: SVGSVGElement,
    graphData: GraphData,
    W: number,
    H: number,
    onNodeClick: (node: GraphNode) => void
  ): d3.Simulation<GraphNode, GraphLink> {
    return this.ngZone.runOutsideAngular(() => {
      const svg = d3.select(svgElement)
        .attr('width', W).attr('height', H);
      svg.selectAll('*').remove();

      // Glow filter
      const defs = svg.append('defs');
      const filter = defs.append('filter').attr('id', 'glow');
      filter.append('feGaussianBlur').attr('stdDeviation', '3.5').attr('result', 'coloredBlur');
      const feMerge = filter.append('feMerge');
      feMerge.append('feMergeNode').attr('in', 'coloredBlur');
      feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

      // Hex dot pattern background (graph mode)
      const patternId = 'hex-dots';
      const pattern = defs.append('pattern')
        .attr('id', patternId).attr('width', 20).attr('height', 20)
        .attr('patternUnits', 'userSpaceOnUse');
      pattern.append('circle').attr('cx', 10).attr('cy', 10).attr('r', 1)
        .attr('fill', '#0D3464').attr('opacity', 0.4);
      svg.append('rect').attr('width', W).attr('height', H)
        .attr('fill', `url(#${patternId})`);

      const nodes: GraphNode[] = graphData.nodes.map(n => ({ ...n }));
      const links: GraphLink[] = graphData.links.map(l => ({ ...l }));

      const simulation = d3.forceSimulation<GraphNode>(nodes)
        .force('link', d3.forceLink<GraphNode, GraphLink>(links)
          .id(d => d.id).distance(110))
        .force('charge', d3.forceManyBody().strength(-320))
        .force('center', d3.forceCenter(W / 2, H / 2))
        .force('collision', d3.forceCollide<GraphNode>(d => d.r + 12));

      const linkEl = svg.append('g').selectAll('line')
        .data(links).join('line')
        .attr('stroke', '#1A6CC0').attr('stroke-opacity', 0.5)
        .attr('stroke-width', 1.5)
        .attr('stroke-dasharray', '4 3');

      const nodeEl = svg.append('g').selectAll<SVGGElement, GraphNode>('g')
        .data(nodes).join('g')
        .style('cursor', 'pointer')
        .call(d3.drag<SVGGElement, GraphNode>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x; d.fy = d.y;
          })
          .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            if (d.type !== 'suite-center' && d.type !== 'project-center') {
              d.fx = null; d.fy = null;
            }
          })
        )
        .on('click', (_event, d) => {
          this.ngZone.run(() => onNodeClick(d));
        });

      nodeEl.append('circle')
        .attr('r', d => d.r)
        .attr('fill', d => `${d.color}22`)
        .attr('stroke', d => d.color)
        .attr('stroke-width', 2)
        .attr('filter', 'url(#glow)');

      nodeEl.append('text')
        .attr('text-anchor', 'middle').attr('dy', '0.35em')
        .attr('fill', '#B0D4EE').attr('font-size', d => d.r > 30 ? 11 : 9)
        .attr('font-family', '"Courier New", monospace')
        .text(d => d.shortLabel);

      simulation.on('tick', () => {
        linkEl
          .attr('x1', d => (d.source as GraphNode).x ?? 0)
          .attr('y1', d => (d.source as GraphNode).y ?? 0)
          .attr('x2', d => (d.target as GraphNode).x ?? 0)
          .attr('y2', d => (d.target as GraphNode).y ?? 0);

        nodeEl.attr('transform', d => `translate(${d.x ?? 0},${d.y ?? 0})`);
      });

      return simulation;
    });
  }

  destroy(simulation: d3.Simulation<any, any> | null): void {
    simulation?.stop();
  }
}
