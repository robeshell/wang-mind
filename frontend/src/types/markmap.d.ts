declare module "markmap-lib" {
  export class Transformer {
    transform(markdown: string): { root: any };
  }
}

declare module "markmap-view" {
  export class Markmap {
    static create(
      svg: SVGElement,
      options: {
        autoFit?: boolean;
        color?: string;
        duration?: number;
      },
      data: any
    ): Markmap;
  }
}

declare module "markmap-view/style/view.css";
