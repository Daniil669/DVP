import { useCallback, useState, useEffect } from "react";
import { ReactFlow, applyNodeChanges, applyEdgeChanges, addEdge, type NodeChange, type Node, type Edge, type EdgeChange, type Connection } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import Offcanvas from 'react-bootstrap/Offcanvas'
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import ListGroup from 'react-bootstrap/ListGroup';
import axios from 'axios';

const rootNodes: Node[] = [
  { id: 'r1', position: { x: 0, y: 0 }, data: { label: 'Root Node' }, type: 'default' },
  { id: 'c1', position: { x: -150, y: 100 }, data: { label: 'Child Node 1' }, type: 'default' },
  { id: 'c2', position: { x: 150, y: 100 }, data: { label: 'Child Node 2' }, type: 'default' }];
  
const initialEdges: Edge[] = [
  { id: 'r1-c1', source: 'r1', target: 'c1' },
  { id: 'r1-c2', source: 'r1', target: 'c2' }
];
interface UsedFile {
  name: string;
  modified_at: number;
  size: number;
}

export default function Graph(){
  const [nodes, setNodes] = useState<Node[]>(rootNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);
  const [show, setShow] = useState(false);
  const [files, setFiles] = useState([]);
  const [filesUsed, setFilesUsed] = useState<UsedFile[]>([]);

  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);

  useEffect(() => {
    axios.get('http://localhost:8000/api/sources', )
      .then(res => {
        console.log("Getting source success", res)
        setFilesUsed(res.data.csv_files)
      })
      .catch(err => console.error("Getting source failed", err));
  }, []);
  
 
  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nodesSnapshot) => applyNodeChanges(changes, nodesSnapshot)),
    [],
  );
  const onEdgesChange = useCallback(
    (changes: EdgeChange<Edge>[]) => setEdges((edgesSnapshot) => applyEdgeChanges(changes, edgesSnapshot)),
    [],
  );

  const onConnect = useCallback(
    (params: Connection) => setEdges((edgesSnapshot) => addEdge(params, edgesSnapshot)),
    [],
  );

  const handleSearch = () => 
  {
    handleClose();
  }
 
  return (
    <div className="graph-page-container">

    <Button variant="primary" onClick={handleShow} style={{ position: 'absolute', top: '10px', left: '10px' }}>
        Open side menu
      </Button>

      <Offcanvas style={{width: '450px'}} show={show} onHide={handleClose}>
        <Offcanvas.Header closeButton>
          <Offcanvas.Title>Manage data</Offcanvas.Title>
        </Offcanvas.Header>
        <Offcanvas.Body>
          <Form>
            <Form.Group className="mb-3" controlId="exampleForm.ControlInput1">
              <Form.Label>Search on the graph</Form.Label>
              <div style={{display: 'flex', gap: '10px'}}>
              <Form.Control type="text" placeholder="Enter the search string" />
              <Button variant="primary" onClick={handleSearch}>Search</Button></div>
            </Form.Group>
          </Form><br/>
          <Form.Label>The list of recent uploaded files:</Form.Label>
          {filesUsed.length > 0 && filesUsed.map(f => 
            <ListGroup style={{width: '380px', cursor: 'pointer'}}>
              <ListGroup.Item>{f.name}</ListGroup.Item>
            </ListGroup>
           )}
           

        </Offcanvas.Body>
      </Offcanvas>
    <div style={{ width: '100vw', height: '100vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      />
    </div>
    </div>
  );
}