import { useCallback, useState } from "react";
import { ReactFlow, applyNodeChanges, applyEdgeChanges, type NodeChange, type Node, type Edge, type EdgeChange } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useLocation } from "react-router-dom";
import axios from "axios";
import type { childNodeResponse } from "../responseTypes";

export default function Graph(){
  const location = useLocation();
  const rootNodeId = location.state?.data[0];
  const [nodes, setNodes] = useState<Node[]>([
    { id: rootNodeId, position: { x: 0, y: 0 }, data: { label: rootNodeId }, type: 'default' }
  ]);
  const [edges, setEdges] = useState<Edge[]>([]);
 
  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nodesSnapshot) => applyNodeChanges(changes, nodesSnapshot)),
    [],
  );
  const onEdgesChange = useCallback(
    (changes: EdgeChange<Edge>[]) => setEdges((edgesSnapshot) => applyEdgeChanges(changes, edgesSnapshot)),
    [],
  );
  const onNodeClick = async (event: React.MouseEvent, node: Node) => {
    const children: childNodeResponse | null = await getChildren(node.id);
    if (!children) {return;}
    const numChildren = children.count_children;
    const spacingX = 200;
    const spacingY = 100;
    let firstX;
    let posY = node.position.y + spacingY;
    if (numChildren % 2 === 0) {
      firstX = node.position.x - ((numChildren / 2 - 0.5) * spacingX);
    }
    else {
      firstX = node.position.x - (((numChildren - 1) / 2) * spacingX);
    }
    const childNodes: Node[] = [];
    const childEdges: Edge[] = [];
    for (let i = 0; i < numChildren; i++) {
      const child = children.children[i];
      const posX = firstX + (i * spacingX);
      const childNode = { id: child.id, position: { x: posX, y: posY }, data: { label: child.id }, type: 'default' };
      const childEdge = { id: `${node.id}-${child.id}`, source: node.id, target: child.id, type: "smoothstep" }
      childNodes.push(childNode);
      childEdges.push(childEdge);
    }
    setNodes(nodes.concat(childNodes));
    setEdges(edges.concat(childEdges));
  }

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
      />
    </div>
  );
}

const getChildren = async (nodeId: string): Promise<childNodeResponse | null> => {
  const resp = axios.get(`http://localhost:8000/api/child_node?node_id=${nodeId}`)
    .then(res => {
      console.log("Children Nodes Received", res.data);
      return res.data; 
    }).catch(err => {
      console.error("Node Retrieval Failed", err);
      return null;
    });
  return resp;
}