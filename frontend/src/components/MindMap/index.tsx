import { useEffect, useRef } from "react";
import G6 from "@antv/g6";

interface MindMapProps {
  data: {
    id: string;
    label: string;
    children?: any[];
  };
}

const MindMap: React.FC<MindMapProps> = ({ data }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>();

  useEffect(() => {
    if (!containerRef.current) return;

    // 配置脑图
    const width = containerRef.current.scrollWidth;
    const height = containerRef.current.scrollHeight || 500;

    if (!graphRef.current) {
      graphRef.current = new G6.Graph({
        container: containerRef.current,
        width,
        height,
        modes: {
          default: ["drag-canvas", "zoom-canvas", "drag-node"],
        },
        layout: {
          type: "mindmap",
          direction: "H",
          getHeight: () => 16,
          getWidth: () => 16,
          getVGap: () => 10,
          getHGap: () => 50,
        },
        defaultNode: {
          type: "rect",
          style: {
            radius: 5,
            padding: [8, 16],
            fill: "#fff",
            stroke: "#91d5ff",
            cursor: "pointer",
          },
        },
        defaultEdge: {
          type: "cubic-horizontal",
          style: {
            stroke: "#91d5ff",
          },
        },
      });
    }

    graphRef.current.data(data);
    graphRef.current.render();

    const handleResize = () => {
      if (graphRef.current && containerRef.current) {
        const { scrollWidth, scrollHeight } = containerRef.current;
        graphRef.current.changeSize(scrollWidth, scrollHeight || 500);
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [data]);

  return <div ref={containerRef} className="w-full h-[500px]" />;
};

export default MindMap;
