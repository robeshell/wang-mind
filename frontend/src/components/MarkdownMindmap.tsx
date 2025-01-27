import React, { useEffect, useRef, useMemo, useCallback } from "react";
import G6 from '@antv/g6';

interface MarkdownMindmapProps {
  markdown: string;
  onRootNodeRendered?: (rootContent: string) => void;
}

interface MindMapNode {
  id: string;
  label: string;
  children?: MindMapNode[];
  type?: string;
  direction?: 'left' | 'right';
  color?: string;
  hover?: boolean;
}

const colorArr = [
  '#5B8FF9', '#5AD8A6', '#5D7092', '#F6BD16', '#6F5EF9',
  '#6DC8EC', '#1E9493', '#FF99C3', '#FF9845', '#945FB9'
];

// 将颜色分配逻辑移到组件外部
const getColorByLevel = (level: number) => {
  if (level === 0) return '#096dd9';
  if (level === 1) return colorArr[0];
  return colorArr[level % colorArr.length];
};

const MarkdownMindmap: React.FC<MarkdownMindmapProps> = React.memo(({ 
  markdown,
  onRootNodeRendered
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);

  // 修改 transformData，使用固定的颜色分配
  const transformData = useCallback((data: MindMapNode, level = 0): MindMapNode => {
    const node = { ...data };
    
    switch (level) {
      case 0:
        node.type = 'dice-mind-map-root';
        break;
      case 1:
        node.type = 'dice-mind-map-sub';
        node.direction = 'right';
        break;
      default:
        node.type = 'dice-mind-map-leaf';
        node.direction = 'right';
    }

    node.hover = false;
    node.color = getColorByLevel(level);

    if (data.children) {
      node.children = data.children.map(child => 
        transformData(child, level + 1)
      );
    }

    return node;
  }, []); // 移除不必要的依赖

  // 添加缓存比较函数
  const memoizedData = useMemo(() => {
    if (!markdown.trim()) return null;
    return transformData(parseMarkdown(markdown), 0);
  }, [markdown]); // 只依赖于 markdown

  // 初始化图形
  useEffect(() => {
    if (!containerRef.current || !memoizedData) return;
    
    // 检查数据变化
    if (graphRef.current) {
      try {
        const currentData = graphRef.current.save();
        if (currentData && currentData.nodes && 
            JSON.stringify(currentData.nodes) === JSON.stringify(memoizedData)) {
          return;
        }
      } catch (error) {
        console.log('Error comparing data:', error);
      }
    }

    // 注册节点和行为
    registerNodes();
    registerBehaviors();

    const width = containerRef.current.scrollWidth;
    const height = containerRef.current.scrollHeight || 600;

    // 销毁旧的图形实例
    if (graphRef.current) {
      graphRef.current.destroy();
    }

    const graph = new G6.TreeGraph({
      container: containerRef.current,
      width,
      height,
      fitView: true,
      fitViewPadding: [20, 40],
      layout: {
        type: 'mindmap',
        direction: 'LR',
        getHeight: () => 16,
        getWidth: (node) => {
          const fontSize = node.level === 0 ? 16 : 12;
          const padding = node.level === 0 ? 24 : 12;
          return G6.Util.getTextSize(node.label, fontSize)[0] + padding;
        },
        getVGap: () => 20,
        getHGap: () => 80,
        getSide: (node) => {
          return node.data.direction || 'right';
        },
        begin: [50, height / 2],
        nodesep: 50,
        ranksep: 80,
        radial: false,
        strictRadial: false,
        preventOverlap: true,
        nodeSize: 20,
        workerEnabled: false
      },
      defaultEdge: {
        type: 'cubic-horizontal',
        style: {
          lineWidth: 2,
          stroke: '#A3B1BF'
        }
      },
      modes: {
        default: ['drag-canvas', 'zoom-canvas', 'dice-mindmap']
      },
      minZoom: 0.5,
      animate: false,  // 初始化时禁用动画
      defaultNode: {
        anchorPoints: [[0, 0.5], [1, 0.5]]
      }
    });

    graphRef.current = graph;
    graph.data(memoizedData);
    
    try {
      graph.render();
      // 渲染完成后启用动画
      setTimeout(() => {
        if (graph && !graph.destroyed) {
          graph.set('animate', true);
        }
      }, 100);
    } catch (error) {
      console.error('Error rendering graph:', error);
    }

    return () => {
      if (graphRef.current && !graphRef.current.destroyed) {
        graphRef.current.destroy();
      }
    };
  }, [memoizedData]);

  return (
    <div ref={containerRef} className="mindmap-container" style={{ width: '100%', height: '600px' }} />
  );
});

MarkdownMindmap.displayName = 'MarkdownMindmap';

export default MarkdownMindmap;

// 将 markdown 解析逻辑提取到单独的函数
function parseMarkdown(markdown: string): MindMapNode {
  const lines = markdown.split('\n').filter(line => line.trim());
  const root: MindMapNode = { 
    id: 'root', 
    label: '', 
    children: [] 
  };
  
  const levelNodes: Record<number, MindMapNode> = {};
  
  lines.forEach((line, index) => {
    const match = line.match(/^(#+)\s+(.+)$/);
    if (match) {
      const level = match[1].length;
      const label = match[2].trim();
      
      const node: MindMapNode = {
        id: `node-${index}`,
        label,
        children: []
      };

      if (level === 1) {
        root.label = label;
        root.id = `node-${index}`;
        levelNodes[1] = root;
      } else {
        const parentLevel = level - 1;
        const parentNode = levelNodes[parentLevel];
        
        if (parentNode) {
          parentNode.children = parentNode.children || [];
          parentNode.children.push(node);
          levelNodes[level] = node;
        }
      }
    }
  });

  return root;
}

// 注册节点和行为的函数定义
function registerNodes() {
  const { Util } = G6;
  
  G6.registerNode('dice-mind-map-root', {
    jsx: (cfg) => {
      const width = Util.getTextSize(cfg.label, 16)[0] + 24;
      const stroke = cfg.style.stroke || '#096dd9';

      return `
      <group>
        <rect draggable="true" style={{width: ${width}, height: 40, stroke: ${stroke}, radius: 4, fill: '#fff', shadowColor: '#ccc', shadowBlur: 10}} keyshape>
          <text style={{ fontSize: 16, marginLeft: 12, marginTop: 12 }}>${cfg.label}</text>
        </rect>
      </group>
    `;
    },
    getAnchorPoints() {
      return [
        [0, 0.5],
        [1, 0.5],
      ];
    },
  });

  G6.registerNode('dice-mind-map-sub', {
    jsx: (cfg) => {
      const width = Util.getTextSize(cfg.label, 14)[0] + 24;
      const color = cfg.color || cfg.style.stroke;

      return `
      <group>
        <rect draggable="true" style={{width: ${width}, height: 35, fill: '#fff', stroke: ${color}, radius: 4}} keyshape>
          <text style={{ fontSize: 14, marginLeft: 12, marginTop: 10 }}>${cfg.label}</text>
        </rect>
      </group>
    `;
    },
    getAnchorPoints() {
      return [
        [0, 0.5],
        [1, 0.5],
      ];
    },
  });

  G6.registerNode('dice-mind-map-leaf', {
    jsx: (cfg) => {
      const width = Util.getTextSize(cfg.label, 12)[0] + 24;
      const color = cfg.color || cfg.style.stroke;

      return `
      <group>
        <rect draggable="true" style={{width: ${width}, height: 30, fill: '#fff', stroke: ${color}, radius: 4}} keyshape>
          <text style={{ fontSize: 12, marginLeft: 12, marginTop: 8 }}>${cfg.label}</text>
        </rect>
      </group>
    `;
    },
    getAnchorPoints() {
      return [
        [0, 0.5],
        [1, 0.5],
      ];
    },
  });
}

function registerBehaviors() {
  // ... 这里是您提供的行为注册代码
}
