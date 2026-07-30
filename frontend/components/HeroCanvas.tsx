"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

const STRAND_POINTS = 60;
const TURNS = 3;
const RADIUS = 1.6;
const HEIGHT = 6;
const RUNG_EVERY = 4;

function readThemeColor(varName: string, fallback: string): THREE.Color {
  if (typeof window === "undefined") return new THREE.Color(fallback);
  const value = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
  try {
    return new THREE.Color(value || fallback);
  } catch {
    return new THREE.Color(fallback);
  }
}

function supportsWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return !!(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

export default function HeroCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !supportsWebGL()) return;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      // No WebGL available despite the feature check above -- fail silently,
      // the existing .ambient-glow gradient behind this component is the fallback.
      return;
    }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    camera.position.set(0, 0, 9);

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const strandAMaterial = new THREE.MeshBasicMaterial({});
    const strandBMaterial = new THREE.MeshBasicMaterial({});
    const rungMaterial = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.35 });

    function applyThemeColors() {
      strandAMaterial.color.copy(readThemeColor("--color-vital-teal", "#0e7c7b"));
      strandBMaterial.color.copy(readThemeColor("--color-pulse-coral", "#e85d4e"));
      rungMaterial.color.copy(strandAMaterial.color);
    }
    applyThemeColors();

    const sphereGeometry = new THREE.SphereGeometry(0.09, 12, 12);
    const strandA = new THREE.InstancedMesh(sphereGeometry, strandAMaterial, STRAND_POINTS);
    const strandB = new THREE.InstancedMesh(sphereGeometry, strandBMaterial, STRAND_POINTS);

    const rungCount = Math.floor(STRAND_POINTS / RUNG_EVERY);
    const rungGeometry = new THREE.CylinderGeometry(0.02, 0.02, RADIUS * 2, 6);
    const rungs = new THREE.InstancedMesh(rungGeometry, rungMaterial, rungCount);

    const helixGroup = new THREE.Group();
    helixGroup.add(strandA, strandB, rungs);
    helixGroup.rotation.x = 0.35;
    scene.add(helixGroup);

    const dummy = new THREE.Object3D();
    let rungIndex = 0;
    for (let i = 0; i < STRAND_POINTS; i++) {
      const t = i / STRAND_POINTS;
      const angle = t * TURNS * Math.PI * 2;
      const y = (t - 0.5) * HEIGHT;

      const ax = Math.cos(angle) * RADIUS;
      const az = Math.sin(angle) * RADIUS;
      dummy.position.set(ax, y, az);
      dummy.updateMatrix();
      strandA.setMatrixAt(i, dummy.matrix);

      const bx = Math.cos(angle + Math.PI) * RADIUS;
      const bz = Math.sin(angle + Math.PI) * RADIUS;
      dummy.position.set(bx, y, bz);
      dummy.updateMatrix();
      strandB.setMatrixAt(i, dummy.matrix);

      if (i % RUNG_EVERY === 0 && rungIndex < rungCount) {
        const midX = (ax + bx) / 2;
        const midZ = (az + bz) / 2;
        dummy.position.set(midX, y, midZ);
        dummy.rotation.z = Math.PI / 2;
        dummy.rotation.y = -angle;
        dummy.updateMatrix();
        rungs.setMatrixAt(rungIndex, dummy.matrix);
        dummy.rotation.set(0, 0, 0);
        rungIndex += 1;
      }
    }

    let frameId: number;
    let visible = true;
    function onVisibilityChange() {
      visible = document.visibilityState === "visible";
    }
    document.addEventListener("visibilitychange", onVisibilityChange);

    function animate() {
      frameId = requestAnimationFrame(animate);
      if (!visible) return;
      helixGroup.rotation.y += 0.0035;
      renderer.render(scene, camera);
    }
    animate();

    function resize() {
      if (!container) return;
      const { clientWidth, clientHeight } = container;
      if (clientWidth === 0 || clientHeight === 0) return;
      camera.aspect = clientWidth / clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(clientWidth, clientHeight);
    }
    resize();
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);

    const themeObserver = new MutationObserver(applyThemeColors);
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });

    return () => {
      cancelAnimationFrame(frameId);
      document.removeEventListener("visibilitychange", onVisibilityChange);
      resizeObserver.disconnect();
      themeObserver.disconnect();
      sphereGeometry.dispose();
      rungGeometry.dispose();
      strandAMaterial.dispose();
      strandBMaterial.dispose();
      rungMaterial.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 -z-10 opacity-70"
    />
  );
}
