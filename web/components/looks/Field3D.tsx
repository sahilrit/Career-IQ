"use client";

import { useEffect, useRef } from "react";

// Dependency-free 3D scene: a perspective-projected particle field flying past
// the camera. Real depth (z-projection), mouse parallax, additive glow. Reads
// as a cinematic 3D tunnel without three.js or any external asset.

type Props = { accent: string; density?: number };

export function Field3D({ accent, density = 260 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let w = 0;
    let h = 0;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resize = () => {
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    window.addEventListener("resize", resize);

    const FOCAL = 620;
    const DEPTH = 1400;
    type P = { x: number; y: number; z: number };
    const rand = (n: number) => (Math.random() - 0.5) * n;
    const stars: P[] = Array.from({ length: density }, () => ({
      x: rand(2200),
      y: rand(1400),
      z: Math.random() * DEPTH + 1,
    }));

    const mouse = { x: 0, y: 0, tx: 0, ty: 0 };
    const onMove = (e: MouseEvent) => {
      mouse.tx = (e.clientX / window.innerWidth - 0.5) * 220;
      mouse.ty = (e.clientY / window.innerHeight - 0.5) * 160;
    };
    window.addEventListener("mousemove", onMove);

    let raf = 0;
    const speed = reduce ? 0 : 3.2;

    const draw = () => {
      mouse.x += (mouse.tx - mouse.x) * 0.05;
      mouse.y += (mouse.ty - mouse.y) * 0.05;
      ctx.clearRect(0, 0, w, h);
      ctx.globalCompositeOperation = "lighter";
      const cx = w / 2 - mouse.x;
      const cy = h / 2 - mouse.y;

      for (const s of stars) {
        s.z -= speed;
        if (s.z < 1) {
          s.x = rand(2200);
          s.y = rand(1400);
          s.z = DEPTH;
        }
        const k = FOCAL / s.z;
        const px = s.x * k + cx;
        const py = s.y * k + cy;
        if (px < -50 || px > w + 50 || py < -50 || py > h + 50) continue;
        const depth = 1 - s.z / DEPTH; // 0 far → 1 near
        const r = Math.max(0.4, depth * 2.6);
        ctx.globalAlpha = 0.15 + depth * 0.8;
        ctx.fillStyle = accent;
        ctx.beginPath();
        ctx.arc(px, py, r, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = "source-over";
      if (!reduce) raf = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMove);
    };
  }, [accent, density]);

  return <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" aria-hidden />;
}
