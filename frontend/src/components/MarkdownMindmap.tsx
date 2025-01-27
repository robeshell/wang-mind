import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import "./MarkdownMindmap.css"; // 我们待会儿创建这个文件

interface MarkdownMindmapProps {
  markdown: string;
}

interface MindMapNode {
  name: string;
  children?: MindMapNode[];
}

const MarkdownMindmap: React.FC<MarkdownMindmapProps> = ({ markdown }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown>>();
  const transformRef = useRef<d3.ZoomTransform>();

  const parseMarkdownToTree = (markdown: string): MindMapNode => {
    // 解码 Unicode 转义序列
    const decodedMarkdown = markdown.replace(/\\u([0-9a-fA-F]{4})/g, (_, hex) =>
      String.fromCharCode(parseInt(hex, 16))
    );

    const lines = decodedMarkdown.split("\n").filter((line) => line.trim());
    const root: MindMapNode = { name: "Root", children: [] };
    let currentLevel: Record<number, MindMapNode> = { 1: root };

    lines.forEach((line) => {
      const match = line.match(/^(#+)\s+(.+?)(?:\uff08(.+?)\uff09)?$/);
      if (match) {
        const level = match[1].length;
        // 如果有括号内的内容，将其作为标签添加到主标题后
        const name = match[3] ? `${match[2]}（${match[3]}）` : match[2];
        const node = { name, children: [] };

        if (!currentLevel[level - 1]) {
          currentLevel[level - 1] = root;
        }

        currentLevel[level - 1].children =
          currentLevel[level - 1].children || [];
        currentLevel[level - 1].children.push(node);
        currentLevel[level] = node;
      } else if (line.startsWith("-")) {
        // 处理列表项
        const name = line.slice(2).trim();
        const lastLevel = Math.max(...Object.keys(currentLevel).map(Number));
        const parent = currentLevel[lastLevel];
        if (parent) {
          parent.children = parent.children || [];
          parent.children.push({ name, children: [] });
        }
      }
    });

    return root.children?.[0] || root;
  };

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;
    const data = parseMarkdownToTree(markdown);

    // 清除旧的内容，但保持缩放状态
    const svg = d3.select(svgRef.current);

    // 只在第一次初始化时设置 SVG 属性
    if (!svg.attr("width")) {
      svg
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [0, 0, width, height]);
    }

    svg.selectAll("g").remove();

    const g = svg
      .append("g")
      .attr(
        "transform",
        transformRef.current?.toString() ||
          `translate(${width / 2},${height / 2})`
      );

    // 创建水平布局的树
    const treeLayout = d3
      .tree<MindMapNode>()
      .size([height - 120, width / 2 - 200])
      .nodeSize([80, 280]);

    const root = d3.hierarchy(data);
    treeLayout(root);

    // 创建曲线生成器
    const diagonal = d3
      .linkHorizontal<any, any>()
      .x((d) => d.y)
      .y((d) => d.x);

    // 绘制连接线
    g.selectAll(".link")
      .data(root.links())
      .join("path")
      .attr("class", (d) => `link link-level-${d.source.depth}`)
      .attr("d", diagonal);

    // 创建节点组
    const node = g
      .selectAll(".node")
      .data(root.descendants())
      .join("g")
      .attr("class", (d) => `node node-level-${d.depth}`)
      .attr("transform", (d) => `translate(${d.y},${d.x})`);

    // 添加节点背景
    node
      .append("rect")
      .attr("class", "node-bg")
      .attr("rx", 6)
      .attr("ry", 6)
      .attr("x", -100)
      .attr("y", -20)
      .attr("width", 200)
      .attr("height", 40);

    // 添加节点文本
    node
      .append("text")
      .attr("dy", "0.3em")
      .attr("text-anchor", "middle")
      .text((d) => d.data.name)
      .each(function () {
        // 文本自动换行
        const text = d3.select(this);
        const words = text.text().split(/(?<=[\u4e00-\u9fa5])|(?<=\s)/g);
        const lineHeight = 1.2;
        const maxWidth = 180;

        let line: string[] = [];
        let lineNumber = 0;
        const tspan = text.text(null).append("tspan").attr("x", 0).attr("y", 0);

        words.forEach((word) => {
          line.push(word);
          tspan.text(line.join(""));
          if ((tspan.node()?.getComputedTextLength() || 0) > maxWidth) {
            line.pop();
            if (line.length) {
              tspan.text(line.join(""));
              line = [word];
              lineNumber++;
              text
                .append("tspan")
                .attr("x", 0)
                .attr("y", 0)
                .attr("dy", `${lineHeight}em`)
                .text(word);
            }
          }
        });

        // 根据文本行数动态调整节点大小
        const parent = d3.select((this as Element).parentNode);
        const rect = parent.select("rect");
        const numLines = text.selectAll("tspan").size();
        const textHeight = numLines * 16 * lineHeight;
        const rectHeight = Math.max(40, textHeight + 16);
        const rectWidth = Math.max(200, maxWidth + 32);

        rect
          .attr("x", -rectWidth / 2)
          .attr("y", -rectHeight / 2)
          .attr("width", rectWidth)
          .attr("height", rectHeight);

        // 调整文本垂直居中
        const totalHeight = numLines * lineHeight * 16;
        text.attr("transform", `translate(0,${-totalHeight / 2 + 16})`);
      });

    // 只在第一次创建缩放行为
    if (!zoomRef.current) {
      zoomRef.current = d3
        .zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.2, 3]) // 调整缩放范围
        .on("zoom", (event) => {
          transformRef.current = event.transform;
          g.attr("transform", event.transform);
        });

      svg.call(zoomRef.current).on("dblclick.zoom", null); // 禁用双击缩放
    }

    // 自动调整缩放以适应内容
    const bounds = g.node()?.getBBox();
    if (bounds) {
      const scale =
        Math.min((width - 80) / bounds.width, (height - 80) / bounds.height) *
        0.95;

      // 只在第一次或内容完全改变时重置视图
      if (!transformRef.current || markdown.length <= 10) {
        const transform = d3.zoomIdentity
          .translate(
            width / 2 - (bounds.x + bounds.width / 2) * scale,
            height / 2 - (bounds.y + bounds.height / 2) * scale
          )
          .scale(scale);

        svg
          .transition()
          .duration(500)
          .call(zoomRef.current!.transform, transform);
        transformRef.current = transform;
      }
    }
  }, [markdown]);

  return (
    <div ref={containerRef} className="markdown-mindmap">
      <svg ref={svgRef} />
    </div>
  );
};

export default MarkdownMindmap;
