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
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import axios from 'axios';
import { useLocation } from 'react-router-dom';
import type { childNodeResponse } from '../responseTypes';
import { TreeLayout } from '../core/TreeLayout';
import CustomNode from './CustomNode';
import { Maximize2, Minimize2, Sun, Moon, Database, Search, FileText, Clock } from 'lucide-react';

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
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [layout, setLayout] = useState<'vertical' | 'horizontal'>('vertical');
  const [searchQuery, setSearchQuery] = useState('');

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
    console.log('Searching for:', searchQuery);
    handleClose();
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const containerStyle: React.CSSProperties = {
    background: theme === 'light' 
      ? 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
      : 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
    minHeight: '100vh',
    transition: 'background 0.3s ease'
  };

  const optionsSectionStyle: React.CSSProperties = {
    background: theme === 'light'
      ? 'rgba(255, 255, 255, 0.95)'
      : 'rgba(45, 45, 45, 0.95)',
    backdropFilter: 'blur(10px)',
    border: theme === 'light' ? '1px solid rgba(255, 255, 255, 0.5)' : '1px solid rgba(68, 68, 68, 0.5)',
    borderRadius: '16px',
    padding: '24px',
    marginBottom: '24px',
    boxShadow: theme === 'light'
      ? '0 8px 32px 0 rgba(31, 38, 135, 0.15)'
      : '0 8px 32px 0 rgba(0, 0, 0, 0.4)',
    transition: 'all 0.3s ease'
  };

  const graphSectionStyle: React.CSSProperties = {
    background: theme === 'light'
      ? 'rgba(255, 255, 255, 0.95)'
      : 'rgba(45, 45, 45, 0.95)',
    backdropFilter: 'blur(10px)',
    border: theme === 'light' ? '1px solid rgba(255, 255, 255, 0.5)' : '1px solid rgba(68, 68, 68, 0.5)',
    borderRadius: '16px',
    boxShadow: theme === 'light'
      ? '0 8px 32px 0 rgba(31, 38, 135, 0.15)'
      : '0 8px 32px 0 rgba(0, 0, 0, 0.4)',
    overflow: 'hidden',
    transition: 'all 0.3s ease'
  };

  const textStyle: React.CSSProperties = {
    color: theme === 'light' ? '#2d3748' : '#e2e8f0'
  };

  const sidebarStyle: React.CSSProperties = {
    background: theme === 'light'
      ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      : 'linear-gradient(135deg, #434343 0%, #000000 100%)',
    color: 'white'
  };

  const getButtonVariant = (targetLayout: 'vertical' | 'horizontal') => {
    if (layout === targetLayout) {
      return theme === 'light' ? 'primary' : 'light';
    }
    return theme === 'light' ? 'outline-secondary' : 'outline-light';
  };

  return (
    <div style={containerStyle}>
      <Offcanvas 
        show={show} 
        onHide={handleClose}
        style={{ 
          width: '450px',
          ...sidebarStyle
        }}
      >
        <Offcanvas.Header closeButton style={{ borderBottom: '1px solid rgba(255,255,255,0.2)', paddingBottom: '20px' }}>
          <Offcanvas.Title style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '1.5rem', fontWeight: 700 }}>
            <Database size={28} />
            Manage Data
          </Offcanvas.Title>
        </Offcanvas.Header>
        <Offcanvas.Body style={{ padding: '24px' }}>
          <div style={{ 
            background: 'rgba(255, 255, 255, 0.15)', 
            backdropFilter: 'blur(10px)',
            borderRadius: '12px', 
            padding: '20px',
            marginBottom: '24px',
            border: '1px solid rgba(255, 255, 255, 0.2)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Search size={20} />
              <span style={{ fontWeight: 600, fontSize: '1.1rem' }}>Search Graph</span>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <Form.Control 
                type="text" 
                placeholder="Enter search query..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  background: 'rgba(255, 255, 255, 0.9)',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '10px 14px'
                }}
              />
              <Button 
                variant="light" 
                onClick={handleSearch}
                style={{
                  borderRadius: '8px',
                  padding: '10px 20px',
                  fontWeight: 600,
                  whiteSpace: 'nowrap'
                }}
              >
                Search
              </Button>
            </div>
          </div>
          <div style={{
            background: 'rgba(255, 255, 255, 0.15)',
            backdropFilter: 'blur(10px)',
            borderRadius: '12px',
            padding: '20px',
            border: '1px solid rgba(255, 255, 255, 0.2)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <FileText size={20} />
              <span style={{ fontWeight: 600, fontSize: '1.1rem' }}>Recent Files</span>
            </div>
            
            {filesUsed.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {filesUsed.map((f, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: 'rgba(255, 255, 255, 0.9)',
                      borderRadius: '8px',
                      padding: '14px 16px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      border: '1px solid transparent'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 1)';
                      e.currentTarget.style.transform = 'translateX(4px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.9)';
                      e.currentTarget.style.transform = 'translateX(0)';
                    }}
                  >
                    <div style={{ fontWeight: 600, color: '#2d3748', marginBottom: '4px' }}>
                      {f.name}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.85rem', color: '#718096' }}>
                      <span>{formatFileSize(f.size)}</span>
                      <span>•</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={14} />
                        {formatDate(f.modified_at)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ 
                textAlign: 'center', 
                padding: '20px',
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: '0.95rem'
              }}>
                No recent files
              </div>
            )}
          </div>
        </Offcanvas.Body>
      </Offcanvas>
      {!isFullscreen && (
        <div style={{ padding: '40px', maxWidth: '1600px', margin: '0 auto' }}>
          <div style={{ marginBottom: '32px', textAlign: 'center' }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              background: theme === 'light'
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : 'linear-gradient(135deg, #434343 0%, #000000 100%)',
              marginBottom: '16px',
              boxShadow: theme === 'light'
                ? '0 4px 20px rgba(102, 126, 234, 0.4)'
                : '0 4px 20px rgba(0, 0, 0, 0.6)'
            }}>
              <Database size={32} color="white" />
            </div>
            <h2 style={{
              ...textStyle,
              fontWeight: 700,
              fontSize: '2rem',
              marginBottom: '8px'
            }}>
              Data Visualization
            </h2>
            <p style={{
              ...textStyle,
              opacity: 0.7,
              fontSize: '1.05rem'
            }}>
              Explore your data through an interactive node graph
            </p>
          </div>


          <div style={optionsSectionStyle}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center', 
              flexWrap: 'wrap', 
              gap: '20px' 
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
                <Button
                  onClick={handleShow}
                  style={{
                    background: theme === 'light'
                      ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                      : 'linear-gradient(135deg, #434343 0%, #000000 100%)',
                    border: 'none',
                    borderRadius: '10px',
                    padding: '10px 20px',
                    color: 'white',
                    fontWeight: 600,
                    boxShadow: theme === 'light'
                      ? '0 4px 15px rgba(102, 126, 234, 0.3)'
                      : '0 4px 15px rgba(0, 0, 0, 0.4)',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = theme === 'light'
                      ? '0 6px 20px rgba(102, 126, 234, 0.4)'
                      : '0 6px 20px rgba(0, 0, 0, 0.5)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = theme === 'light'
                      ? '0 4px 15px rgba(102, 126, 234, 0.3)'
                      : '0 4px 15px rgba(0, 0, 0, 0.4)';
                  }}
                >
                  <Database size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                  Manage Data
                </Button>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ ...textStyle, fontWeight: 500, fontSize: '0.95rem' }}>Layout:</span>
                  <ButtonGroup size="sm">
                    <Button
                      variant={getButtonVariant('vertical')}
                      onClick={() => setLayout('vertical')}
                      style={{ 
                        borderRadius: '8px 0 0 8px',
                        fontWeight: 500,
                        padding: '8px 16px'
                      }}
                    >
                      Vertical
                    </Button>
                    <Button
                      variant={getButtonVariant('horizontal')}
                      onClick={() => setLayout('horizontal')}
                      style={{ 
                        borderRadius: '0 8px 8px 0',
                        fontWeight: 500,
                        padding: '8px 16px'
                      }}
                    >
                      Horizontal
                    </Button>
                  </ButtonGroup>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ ...textStyle, fontWeight: 500, fontSize: '0.95rem' }}>Theme:</span>
                  <Button
                    variant={theme === 'light' ? 'outline-secondary' : 'outline-light'}
                    size="sm"
                    onClick={toggleTheme}
                    style={{
                      borderRadius: '8px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      fontWeight: 500,
                      padding: '8px 16px'
                    }}
                  >
                    {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
                    {theme === 'light' ? 'Dark' : 'Light'}
                  </Button>
                </div>
              </div>
              <Button
                variant={theme === 'light' ? 'outline-secondary' : 'outline-light'}
                size="sm"
                onClick={toggleFullscreen}
                style={{
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontWeight: 500,
                  padding: '8px 16px'
                }}
              >
                <Maximize2 size={16} />
                Fullscreen
              </Button>
            </div>
          </div>

          <div style={{ ...graphSectionStyle, height: '650px' }}>
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
      )}

      {isFullscreen && (
        <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
          <Button
            onClick={toggleFullscreen}
            style={{
              position: 'absolute',
              top: '16px',
              right: '16px',
              zIndex: 1000,
              background: theme === 'light'
                ? 'rgba(255, 255, 255, 0.95)'
                : 'rgba(45, 45, 45, 0.95)',
              backdropFilter: 'blur(10px)',
              border: 'none',
              borderRadius: '10px',
              padding: '10px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontWeight: 600,
              color: theme === 'light' ? '#2d3748' : '#e2e8f0',
              boxShadow: '0 4px 15px rgba(0, 0, 0, 0.2)'
            }}
          >
            <Minimize2 size={16} />
            Exit Fullscreen
          </Button>
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
      )}
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