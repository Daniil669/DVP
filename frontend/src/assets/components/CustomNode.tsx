import React from 'react';
import { Handle, Position } from '@xyflow/react';
import './CustomNode.css';

export default function CustomNode({ data }: any) {
  const { label, hasChildren, expanded } = data;

  return (
    <div className={`custom-node ${hasChildren && !expanded ? 'glow' : ''}`}>
      <Handle type="target" position={Position.Top} />
      <div className="custom-node-content">{label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
