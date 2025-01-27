declare module "@antv/g6" {
  export interface GraphData {
    id: string;
    label: string;
    children?: GraphData[];
  }
}
