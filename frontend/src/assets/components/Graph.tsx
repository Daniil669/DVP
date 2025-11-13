import { useCallback, useState, useEffect } from 'react';
import {
  ReactFlow,
  applyNodeChanges,
  applyEdgeChanges,
  type NodeChange,
  type Node,
  type Edge,
  type EdgeChange
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import Offcanvas from 'react-bootstrap/Offcanvas';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import ListGroup from 'react-bootstrap/ListGroup';
import axios from 'axios';
import { useLocation } from 'react-router-dom';
import type { childNodeResponse } from '../responseTypes';
import { TreeLayout } from '../core/TreeLayout';
import CustomNode from './CustomNode';

interface UsedFile {
  name: string;
  modified_at: number;
  size: number;
}

const connection_id = 1;
let treeLayout: TreeLayout;

const nodeTypes = {
  customNode: CustomNode
};

export default function Graph() {
  const location = useLocation();
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [show, setShow] = useState(false);
  const [filesUsed, setFilesUsed] = useState<UsedFile[]>([]);

  const rootNodeId = location.state?.nodes[0];
  const dataset_id = location.state?.fileData;

  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);

  useEffect(() => {
    axios
      .get('http://localhost:8000/api/sources')
      .then(res => {
        console.log('Getting source success', res);
        setFilesUsed(res.data.csv_files);
      })
      .catch(err => console.error('Getting source failed', err));
    treeLayout = new TreeLayout(
      {
        id: rootNodeId,
        name: rootNodeId,
        children: []
      },
      [120, 40],
      50
    );
  }, []);

  useEffect(() => {
    const [initNodes, initEdges] = treeLayout.getTreeLayout();
    setNodes(initNodes);
    setEdges(initEdges);
    console.log(initNodes, initEdges);
  }, []);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes(nodesSnapshot => applyNodeChanges(changes, nodesSnapshot)),
    []
  );
  const onEdgesChange = useCallback(
    (changes: EdgeChange<Edge>[]) => setEdges(edgesSnapshot => applyEdgeChanges(changes, edgesSnapshot)),
    []
  );
  const onNodeClick = async (_event: React.MouseEvent, node: Node) => {
    const isExpanded = treeLayout.isExpanded(node.id);
    if (!isExpanded) {
      const children: childNodeResponse | null = await getChildren(node.id, dataset_id);
      if (!children) return;
      const childrenNodes = children.children.map(child => {
        return {
          id: child.id,
          name: child.name,
          children: [],
          hasChildren: child.has_children ?? false
        };
      });
      treeLayout.expandNode(node.id, childrenNodes);
      const [newNodes, newEdges] = treeLayout.getTreeLayout();
      setNodes(newNodes);
      setEdges(newEdges);
    } else {
      treeLayout.collapseNode(node.id);
      const [newNodes, newEdges] = treeLayout.getTreeLayout();
      setNodes(newNodes);
      setEdges(newEdges);
    }
  };

  const handleSearch = () => {
    handleClose();
  };

  return (
    <div className="graph-page-container">
      <Button variant="primary" onClick={handleShow} style={{ position: 'absolute', top: '10px', left: '10px' }}>
        Open side menu
      </Button>

      <Offcanvas style={{ width: '450px' }} show={show} onHide={handleClose}>
        <Offcanvas.Header closeButton>
          <Offcanvas.Title>Manage data</Offcanvas.Title>
        </Offcanvas.Header>
        <Offcanvas.Body>
          <Form>
            <Form.Group className="mb-3" controlId="exampleForm.ControlInput1">
              <Form.Label>Search on the graph</Form.Label>
              <div style={{ display: 'flex', gap: '10px' }}>
                <Form.Control type="text" placeholder="Enter the search string" />
                <Button variant="primary" onClick={handleSearch}>
                  Search
                </Button>
              </div>
            </Form.Group>
          </Form>
          <br />
          <Form.Label>The list of recent uploaded files:</Form.Label>
          {filesUsed.length > 0 &&
            filesUsed.map(f => (
              <ListGroup style={{ width: '380px', cursor: 'pointer' }}>
                <ListGroup.Item>{f.name}</ListGroup.Item>
              </ListGroup>
            ))}
        </Offcanvas.Body>
      </Offcanvas>
      <div style={{ width: '100vw', height: '100vh' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          fitView
        />
      </div>
    </div>
  );
}

const getChildren = async (nodeId: string, dataset_id: number): Promise<childNodeResponse | null> => {
  const resp = axios
    .get(
      `http://localhost:8000/api/child_node?connection_id=${connection_id}&dataset_id=${dataset_id}&node_id=${nodeId}`,
      {
        headers: {
          'x-api-key': 'secret123'
        }
      }
    )
    .then(res => {
      console.log('Children Nodes Received', res.data);
      return res.data;
    })
    .catch(err => {
      console.error('Node Retrieval Failed', err);
      return null;
    });
  return resp;
};
