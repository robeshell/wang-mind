declare module "@antv/g6" {
  const G6: {
    Graph: any;
    registerNode: (type: string, options: any) => void;
    registerEdge: (type: string, options: any) => void;
    registerBehavior: (type: string, options: any) => void;
    registerLayout: (type: string, options: any) => void;
  };
  export default G6;
}
