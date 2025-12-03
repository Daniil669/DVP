import type { Edge, Node } from '@xyflow/react';
import * as d3 from 'd3-hierarchy';
import type { nodeInPath } from '../responseTypes';

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
    this.updateTree();
  }

  private updateTree() {
    this.treeLayout(this.root);
    this.nodes = [];
    this.edges = [];

    this.root.descendants().forEach(d => {
      const declaredNum = d.data.numChildren;
      const localChildrenCount = (d.data.children?.length ?? 0);
      let hasChildren = false;
      if (declaredNum) {
        hasChildren = declaredNum > localChildrenCount;
      }

      if (d.parent) {
        this.edges.push({
          id: `${d.parent.data.id}-${d.data.id}`,
          source: d.parent.data.id,
          target: d.data.id
        });
      }

      const expanded = this.isExpanded(d.data.id);
      this.nodes.push({
        id: d.data.id,
        data: { label: d.data.name, numChildren: declaredNum, hasChildren, expanded },
        position: { x: d.x, y: d.y },
        style: { width: this.nodeWidth, height: this.nodeHeight },
        type: 'customNode'
      });
    });
  }

  public expandNode(nodeId: string, childData: any[]) {
    const target = this.root.descendants().find(d => d.data.id === nodeId);
    if (!target) return;
    if (!target.data.children) target.data.children = [];

    const existingIds = new Set((target.data.children ?? []).map((c: any) => c.id));
    const newChildren = childData.filter((child) => !existingIds.has(child.id));

    target.data.children.push(...newChildren);

    this.root = d3.hierarchy(this.root.data);
    this.updateTree();
  }

  public collapseNode(nodeId: string) {
    const target = this.root.descendants().find(d => d.data.id === nodeId);
    if (!target) return;
    target.data.children = [];
    this.root = d3.hierarchy(this.root.data);
    this.updateTree();
  }

  public getTreeLayout(): [Node[], Edge[]] {
    return [this.nodes, this.edges];
  }

  public isExpanded(nodeId: string): boolean {
    const target = this.root.descendants().find(d => d.data.id === nodeId);
    return (target?.data.children?.length ?? 0) > 0;
  }

  public numberOfChildren(nodeId: string): number {
    const target = this.root.descendants().find(d => d.data.id === nodeId);
    return target?.data.children?.length;
  }

  public expandPath(path: nodeInPath[]) {
    path.forEach((node: nodeInPath) => {
      if (node.child_id === "") return;
      const child = {
        id: node.child_id,
        name: node.child_name,
        children: [],
        hasChildren: false
      };
      this.expandNode(node.id, [child]);
    })
  }
}
