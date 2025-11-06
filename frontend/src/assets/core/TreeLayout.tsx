import type { Edge, Node } from '@xyflow/react';
import * as d3 from 'd3-hierarchy';

export class TreeLayout {
  root: d3.HierarchyNode<any>;
  treeLayout: d3.TreeLayout<any>;
  nodeWidth: number;
  nodeHeight: number;
  spacing: number;
  nodes: any[];
  edges: any[];

  constructor(data: any, nodeSize: [number, number], spacing: number) {
    this.root = d3.hierarchy(data);
    [this.nodeWidth, this.nodeHeight] = nodeSize;
    this.spacing = spacing;
    this.treeLayout = d3.tree().nodeSize([this.nodeWidth + this.spacing, this.nodeHeight + this.spacing]);
    this.nodes = [];
    this.edges = [];
    console.log('');
    this.updateTree();
  }

  private updateTree() {
    this.treeLayout(this.root);
    this.nodes = [];
    this.edges = [];

    this.root.descendants().forEach(d => {
      this.nodes.push({
        id: d.data.id,
        data: { label: d.data.name },
        position: { x: d.x, y: d.y },
        style: { width: this.nodeWidth, height: this.nodeHeight },
        type: 'default'
      });

      if (d.parent) {
        this.edges.push({
          id: `${d.parent.data.id}-${d.data.id}`,
          source: d.parent.data.id,
          target: d.data.id
        });
      }
    });
    console.log(this.root);
  }

  public expandNode(nodeId: string, childData: any[]) {
    const target = this.root.descendants().find(d => d.data.id === nodeId);
    if (!target) return;
    if (!target.data.children) {
      target.data.children = [];
    } else if (target.data.children.length > 0) return;

    target.data.children.push(...childData);
    this.root = d3.hierarchy(this.root.data);
    this.updateTree();
  }

  public getTreeLayout(): [Node[], Edge[]] {
    return [this.nodes, this.edges];
  }
}
