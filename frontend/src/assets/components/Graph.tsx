import { useCallback, useState, useEffect, type ChangeEvent } from 'react';
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
import { useNavigate, useSearchParams } from 'react-router-dom';
import type { childNodeResponse, DatasetInfo, DatasetsByConnection, sourcesResponse } from '../responseTypes';
import { TreeLayout } from '../core/TreeLayout';
import CustomNode from './CustomNode';
import { nodeService, sourceService } from '../services/service-instances';
import { Modal } from 'react-bootstrap';

type formattedSource = {
  connectionId: number,
  datasetId: number,
  originalName: string,
}

let treeLayout: TreeLayout;

const nodeTypes = {
  customNode: CustomNode
};

export default function Graph() {
  const navigate = useNavigate();
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [show, setShow] = useState(false);
  const [filesUsed, setFilesUsed] = useState<formattedSource[]>([]);
  const [searchString, setSearchString] = useState<string>('');
  const [showConfirm, setShowConfirm] = useState(false);
  const [selectedSource, setSelectedSource] = useState<formattedSource>();
  const [numberChildren, setNumberChildren] = useState<number | null>(null);

  const [searchParams] = useSearchParams();
  const datasetId = parseInt(searchParams.get("datasetId")!);

  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);
  const handleCloseConfirmation = () => {
    setSelectedSource(undefined);
    setShowConfirm(false);
  }
  const handleShowConfirmation = (source: formattedSource) => {
    setSelectedSource(source);
    setShowConfirm(true);
  }

  useEffect(() => {
    sourceService.getSources().then(res => {
      if (res) {
        setFilesUsed(formatSources(res, datasetId));
      }
    });
    nodeService.getRootNode(datasetId).then(res => {
      const rootNodeId = res?.root_nodes[0];
      treeLayout = new TreeLayout(
        {
          id: rootNodeId,
          name: rootNodeId,
          children: []
        },
        [120, 40],
        50
      );
      const [initNodes, initEdges] = treeLayout.getTreeLayout();
      setNodes(initNodes);
      setEdges(initEdges);
    });
  }, [datasetId]);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes(nodesSnapshot => applyNodeChanges(changes, nodesSnapshot)),
    []
  );
  const onEdgesChange = useCallback(
    (changes: EdgeChange<Edge>[]) => setEdges(edgesSnapshot => applyEdgeChanges(changes, edgesSnapshot)),
    []
  );
  const onNodeClick = async (_event: React.MouseEvent, node: Node) => {
    const childrenExpanded = treeLayout.numberOfChildren(node.id)
    const childrenToFetch = numberChildren ? (numberChildren + childrenExpanded) : null;
    const children: childNodeResponse | null = await nodeService.getChildNodes(datasetId, node.id, childrenToFetch);
    if (!children) return;
    const fullyExpanded = children.count_children === childrenExpanded;
    if (!fullyExpanded) {
      const childrenNodes = children.children.map(child => {
        return {
          id: child.id,
          name: child.name,
          children: [],
          numChildren: child.num_children ?? 0
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

  const handleNewSource = async () => {
    if (!selectedSource) {
      console.error("Hmmm, no new source has been selected");
      return;
    }
    navigate(`/graph?datasetId=${selectedSource.datasetId}`);
    handleCloseConfirmation();
    handleClose();
  }

  const handleSearch = async (nodeId: string) => {
    const pathResp = await nodeService.getNodePath(datasetId, nodeId);
    if (!pathResp) return;

    treeLayout.expandPath(pathResp.path.path);
    const [newNodes, newEdges] = treeLayout.getTreeLayout();
    setNodes(newNodes);
    setEdges(newEdges);
    handleClose();
  };

  function handleOnChange(event: ChangeEvent<HTMLInputElement>): void {
    setSearchString(event.target.value);
  }
  
  const handleNumChildrenChange = (event: ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value == '101' ? null : parseInt(event.target.value)
    setNumberChildren(value);
  }

  return (
    <div className="graph-page-container">
      <Button variant="primary" onClick={handleShow} style={{ position: 'absolute', top: '10px', left: '10px' }}>
        Open side menu
      </Button>

      <Modal show={showConfirm} onHide={handleCloseConfirmation}>
        <Modal.Header closeButton>
          <Modal.Title>Switch sources</Modal.Title>
        </Modal.Header>
        <Modal.Body>Are you sure you would like to switch sources</Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseConfirmation}>
            Keep this source
          </Button>
          <Button variant="primary" onClick={handleNewSource}>
            Change to new source
          </Button>
        </Modal.Footer>
      </Modal>

      <Offcanvas style={{ width: '450px' }} show={show} onHide={handleClose}>
        <Offcanvas.Header closeButton>
          <Offcanvas.Title>Manage data</Offcanvas.Title>
        </Offcanvas.Header>
        <Offcanvas.Body>
          <Form.Label>
            Number of Children to Expand
          </Form.Label>
          <Form.Range
            value={numberChildren ?? 101}
            name='hello'
            onChange={handleNumChildrenChange}
            min={1}
            max={101}
            step={1}
          />
          <p>Fetch {numberChildren ?? 'ALL'} children</p>
          <Form>
            <Form.Group className="mb-3" controlId="exampleForm.ControlInput1">
              <Form.Label>Search on the graph</Form.Label>
              <div style={{ display: 'flex', gap: '10px' }}>
                <Form.Control type="text" placeholder="Enter the search string" onChange={handleOnChange}/>
                <Button variant="primary" onClick={() => handleSearch(searchString)}>
                  Search
                </Button>
              </div>
            </Form.Group>
          </Form>
          <br />
          <Form.Label>The list of recent uploaded files:</Form.Label>
          
          <ListGroup style={{ width: '380px' }}>
            {filesUsed.length > 0 && filesUsed.map(f => (
              <ListGroup.Item action onClick={() => handleShowConfirmation(f)}>{f.originalName}</ListGroup.Item>
            ))}
          </ListGroup>
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

const formatSources = (sources: sourcesResponse, currentDataset: number) => {
  const response: formattedSource[] = [];
  sources.datasets_by_connection.forEach((connection: DatasetsByConnection) => {
    connection.datasets.forEach((dataset: DatasetInfo) => {
      if (dataset.dataset_id !== currentDataset) 
        response.push({
          connectionId: connection.connection_id,
          datasetId: dataset.dataset_id,
          originalName: dataset.original_name
        })
      }
    )
  });
  return response;
}
