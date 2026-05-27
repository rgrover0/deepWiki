import { Injectable, inject } from '@angular/core';
import { Suite, Project, GraphData, GraphNode, GraphLink, GraphLevel } from '../models';

// Suite colors for the cosmos graph
const SUITE_COLORS = [
  '#2878CC', '#1D9E75', '#8870DD', '#FFD100', '#e74c3c',
];

@Injectable({ providedIn: 'root' })
export class GraphDataService {

  buildCosmosGraph(suites: Suite[], W: number, H: number): GraphData {
    const cx = W / 2, cy = H / 2;
    const nodes: GraphNode[] = [];
    const links: GraphLink[] = [];

    suites.forEach((suite, si) => {
      const angle  = (si / suites.length) * 2 * Math.PI - Math.PI / 2;
      const radius = Math.min(W, H) * 0.28;
      const color  = suite.color ?? SUITE_COLORS[si % SUITE_COLORS.length];

      const centerNode: GraphNode = {
        id:         `suite-${suite.id}`,
        label:      suite.name,
        shortLabel: suite.name.split(' ')[0],
        type:       'suite-center',
        color,
        r:          42,
        data:       suite,
        fx:         cx + radius * Math.cos(angle),
        fy:         cy + radius * Math.sin(angle),
      };
      nodes.push(centerNode);

      suite.projects.forEach((project, pi) => {
        const pAngle  = angle + ((pi - (suite.projects.length - 1) / 2) * 0.4);
        const pRadius = radius * 0.55;
        const pNode: GraphNode = {
          id:         `project-${project.id}`,
          label:      project.name,
          shortLabel: project.name.split(' ')[0],
          type:       'project',
          color,
          r:          24,
          data:       project,
          x:          cx + (radius + pRadius) * Math.cos(pAngle),
          y:          cy + (radius + pRadius) * Math.sin(pAngle),
        };
        nodes.push(pNode);
        links.push({ source: centerNode.id, target: pNode.id, type: 'owns' });
      });
    });

    return { nodes, links };
  }

  buildSuiteGraph(suiteId: string, suites: Suite[], W: number, H: number): GraphData {
    const suite = suites.find(s => s.id === suiteId);
    if (!suite) return { nodes: [], links: [] };

    const cx = W / 2, cy = H / 2;
    const nodes: GraphNode[] = [];
    const links: GraphLink[] = [];
    const color = suite.color ?? SUITE_COLORS[0];

    const centerNode: GraphNode = {
      id: `suite-${suite.id}`, label: suite.name, shortLabel: suite.name,
      type: 'suite-center', color, r: 50, data: suite, fx: cx, fy: cy,
    };
    nodes.push(centerNode);

    suite.projects.forEach((project, pi) => {
      const angle   = (pi / suite.projects.length) * 2 * Math.PI - Math.PI / 2;
      const radius  = Math.min(W, H) * 0.3;
      const pNode: GraphNode = {
        id:         `project-${project.id}`,
        label:      project.name,
        shortLabel: project.name.split(' ')[0],
        type:       'project',
        color,
        r:          32,
        data:       project,
        x:          cx + radius * Math.cos(angle),
        y:          cy + radius * Math.sin(angle),
      };
      nodes.push(pNode);
      links.push({ source: centerNode.id, target: pNode.id, type: 'owns' });
    });

    return { nodes, links };
  }

  buildProjectGraph(projectId: string, suites: Suite[], W: number, H: number): GraphData {
    let project: Project | undefined;
    for (const s of suites) {
      project = s.projects.find(p => p.id === projectId);
      if (project) break;
    }
    if (!project) return { nodes: [], links: [] };

    const cx = W / 2, cy = H / 2;
    const nodes: GraphNode[] = [];
    const links: GraphLink[] = [];

    const centerNode: GraphNode = {
      id: `project-center-${project.id}`, label: project.name, shortLabel: project.name,
      type: 'project-center', color: '#2878CC', r: 44, data: project, fx: cx, fy: cy,
    };
    nodes.push(centerNode);

    project.modules.forEach((mod, mi) => {
      const angle  = (mi / project!.modules.length) * 2 * Math.PI - Math.PI / 2;
      const radius = Math.min(W, H) * 0.28;
      const mNode: GraphNode = {
        id:         `module-${mod.id}`,
        label:      mod.name,
        shortLabel: mod.name.split(' ')[0],
        type:       'module',
        color:      '#1D9E75',
        r:          22,
        data:       mod,
        x:          cx + radius * Math.cos(angle),
        y:          cy + radius * Math.sin(angle),
      };
      nodes.push(mNode);
      links.push({ source: centerNode.id, target: mNode.id, type: 'owns' });
    });

    return { nodes, links };
  }
}
