import React from 'react';
import { Handle, Position } from '@xyflow/react';
import './CustomNode.css';

export default function CustomNode({ data }: any) {
  const { label, hasChildren, expanded, layout = 'horizontal' } = data;

  const targetPosition = layout === 'horizontal' ? Position.Left : Position.Top;
  const sourcePosition = layout === 'horizontal' ? Position.Right : Position.Bottom;

  return (
    <div className={`custom-node ${hasChildren && !expanded ? 'glow' : ''}`}>
      <Handle type="target" position={targetPosition} />
      <div className="custom-node-content">{label}</div>
      <Handle type="source" position={sourcePosition} />
    </div>
  );
}