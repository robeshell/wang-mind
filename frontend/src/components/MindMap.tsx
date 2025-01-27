import React, { useEffect, useCallback, useState } from "react";
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionLineType,
  Panel,
  Handle,
  Position,
} from "reactflow";
import dagre from "dagre";
import ReactMarkdown from "react-markdown";
import "reactflow/dist/style.css";
import { MindMapNode as MindMapNodeType } from "../api/mindmap";

// Markdown 解析函数
const parseMarkdownToMindMap = (markdown: string) => {
  const lines = markdown.split("\n").filter((line) => line.trim());
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  let parentStack: Node[] = [];
  let nodeId = 0;

  lines.forEach((line) => {
    if (!line.startsWith("#")) return;

    const level = line.match(/^#+/)[0].length;
    const content = line.replace(/^#+\s+/, "").trim();
    const id = `node-${nodeId++}`;

    const node: Node = {
      id,
      type: "mindmap",
      data: {
        label: content,
        level,
        color: getNodeColor(level - 1),
        hasChildren: false,
      },
      position: { x: 0, y: 0 },
    };

    nodes.push(node);

    // 根据层级关系创建边
    while (parentStack.length >= level) {
      parentStack.pop();
    }

    if (parentStack.length > 0) {
      const parent = parentStack[parentStack.length - 1];
      parent.data.hasChildren = true;
      edges.push({
        id: `edge-${parent.id}-${id}`,
        source: parent.id,
        target: id,
        type: "mindmap",
        sourceHandle: "right",
        targetHandle: "left",
      });
    }

    parentStack.push(node);
  });

  return { nodes, edges };
};

const getNodeColor = (level: number) => {
  const colors = ["#ffffff", "#f0f7ff", "#fff7e6", "#f6ffed"];
  return colors[level % colors.length];
};

// 自定义节点组件
const MindMapNode = ({ data }: any) => {
  return (
    <div
      style={{
        padding: "12px 20px",
        borderRadius: "8px",
        background: data.color || "#ffffff",
        border: "1px solid #e0e0e0",
        fontSize: "14px",
        maxWidth: "300px",
        textAlign: "left",
        boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        id="left"
        style={{
          background: "#888",
          width: 6,
          height: 6,
          borderRadius: 3,
          opacity: 0.7,
        }}
      />
      <ReactMarkdown>{data.label}</ReactMarkdown>
      {data.hasChildren && (
        <Handle
          type="source"
          position={Position.Right}
          id="right"
          style={{
            background: "#888",
            width: 6,
            height: 6,
            borderRadius: 3,
            opacity: 0.7,
          }}
        />
      )}
    </div>
  );
};

// 自定义边组件
const MindMapEdge = ({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition = Position.Right,
  targetPosition = Position.Left,
  style = {},
}: any) => {
  const midX = (sourceX + targetX) / 2;

  return (
    <g>
      <path
        d={`M ${sourceX} ${sourceY} L ${midX} ${sourceY} L ${midX} ${targetY} L ${targetX} ${targetY}`}
        fill="none"
        stroke="#888"
        strokeWidth={2}
        {...style}
      />
    </g>
  );
};

// 节点类型定义
const nodeTypes = {
  mindmap: MindMapNode,
};

// 边类型定义
const edgeTypes = {
  mindmap: MindMapEdge,
};

// 使用 dagre 布局算法
const getLayoutedElements = (
  nodes: Node[],
  edges: Edge[],
  direction = "LR"
) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 100,
    ranksep: 150,
    marginx: 50,
    marginy: 50,
    edgesep: 50,
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 200, height: 60 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  return {
    nodes: nodes.map((node) => {
      const nodeWithPosition = dagreGraph.node(node.id);
      return {
        ...node,
        position: {
          x: nodeWithPosition.x - 100,
          y: nodeWithPosition.y - 30,
        },
      };
    }),
    edges: edges.map((edge) => ({
      ...edge,
      type: "mindmap", // 使用自定义边类型
      style: {
        stroke: "#888",
        strokeWidth: 2,
      },
    })),
  };
};

interface MindMapProps {
  markdown: string;
}

export const MindMap: React.FC<MindMapProps> = ({ markdown }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [prevNodeIds] = useState(new Set<string>());

  // 获取节点深度
  const getNodeDepth = useCallback(
    (node: MindMapNodeType, root: MindMapNodeType): number => {
      if (node === root) return 0;
      let depth = 0;
      const findDepth = (
        currentNode: MindMapNodeType,
        targetId: string,
        currentDepth: number
      ): number => {
        if (currentNode.id === targetId) return currentDepth;
        if (!currentNode.children) return -1;
        for (const child of currentNode.children) {
          const result = findDepth(child, targetId, currentDepth + 1);
          if (result !== -1) return result;
        }
        return -1;
      };
      depth = findDepth(root, node.id, 0);
      return depth === -1 ? 0 : depth;
    },
    []
  );

  // 获取节点颜色
  const getNodeColor = useCallback((depth: number) => {
    const colors = ["#ffffff", "#f0f7ff", "#fff7e6", "#f6ffed"];
    return colors[depth % colors.length];
  }, []);

  const processData = useCallback(
    (mindmapData: MindMapNodeType) => {
      const nodes: Node[] = [];
      const edges: Edge[] = [];
      const currentNodeIds = new Set<string>();

      const processNode = (
        node: MindMapNodeType,
        parentId: string | null = null
      ) => {
        const nodeId = node.id;
        currentNodeIds.add(nodeId);
        const hasChildren = node.children && node.children.length > 0;
        const isNew = !prevNodeIds.has(nodeId);

        nodes.push({
          id: nodeId,
          type: "mindmap",
          position: { x: 0, y: 0 },
          data: {
            label: node.label,
            color: getNodeColor(getNodeDepth(node, mindmapData)),
            hasChildren,
            isNew,
          },
        });

        if (parentId) {
          const edgeId = `edge-${parentId}-${nodeId}`;
          edges.push({
            id: edgeId,
            source: parentId,
            target: nodeId,
            sourceHandle: "right",
            targetHandle: "left",
            type: "smoothstep",
            style: {
              stroke: "#888",
              strokeWidth: 2,
              opacity: isNew ? 0.5 : 0.7,
            },
            animated: isNew,
          });
        }

        if (hasChildren) {
          node.children.forEach((child) => processNode(child, nodeId));
        }
      };

      processNode(mindmapData);
      setPrevNodeIds(currentNodeIds);
      return getLayoutedElements(nodes, edges, "LR");
    },
    [getNodeColor, getNodeDepth, prevNodeIds]
  );

  useEffect(() => {
    if (markdown) {
      const { nodes: initialNodes, edges: initialEdges } =
        parseMarkdownToMindMap(markdown);
      const { nodes: layoutedNodes, edges: layoutedEdges } =
        getLayoutedElements(initialNodes, initialEdges);
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    }
  }, [markdown]);

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        minHeight: "600px",
        flex: 1,
        display: "flex",
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{
          padding: 0.2,
          includeHiddenNodes: true,
        }}
        minZoom={0.5}
        maxZoom={1.5}
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        style={{
          width: "100%",
          height: "100%",
          background: "#fafafa",
        }}
      >
        <Controls />
        <Background color="#f0f0f0" gap={16} />
        <MiniMap
          nodeColor={(node) => node.data.color}
          maskColor="rgba(255, 255, 255, 0.8)"
          style={{
            background: "#ffffff",
            border: "1px solid #eee",
          }}
        />
        <Panel position="top-right">
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: "8px 12px",
              background: "#fff",
              border: "1px solid #ddd",
              borderRadius: "4px",
              cursor: "pointer",
              boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
            }}
          >
            重置视图
          </button>
        </Panel>
      </ReactFlow>
    </div>
  );
};
