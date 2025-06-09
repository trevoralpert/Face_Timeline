declare module 'gsap' {
  interface GSAPTimeline {
    to(targets: any, vars: any): GSAPTimeline;
    from(targets: any, vars: any): GSAPTimeline;
    kill(): void;
  }

  interface GSAPStatic {
    timeline(vars?: any): GSAPTimeline;
    to(targets: any, vars: any): GSAPTimeline;
    from(targets: any, vars: any): GSAPTimeline;
    registerPlugin(...args: any[]): void;
  }

  const gsap: GSAPStatic;
  export { gsap };
  export function timeline(vars?: any): GSAPTimeline;
}

declare module 'gsap/ScrollTrigger' {
  interface ScrollTriggerInstance {
    kill(): void;
    enable(): void;
    disable(): void;
  }

  interface ScrollTriggerStatic {
    create(vars: any): ScrollTriggerInstance;
    refresh(): void;
    update(): void;
    clearScrollMemory(): void;
    enable(): void;
    disable(): void;
  }

  export const ScrollTrigger: ScrollTriggerStatic;
} 