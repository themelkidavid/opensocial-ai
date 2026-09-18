import type { ReactNode } from "react";

export function Notice({ children, kind = "info" }: { children: ReactNode; kind?: "info" | "error" | "success" }) { return <div role={kind === "error" ? "alert" : "status"} className={`notice ${kind}`}>{children}</div>; }
export function Card({ title, children }: { title?: string; children: ReactNode }) { return <section className="card">{title && <h2>{title}</h2>}{children}</section>; }
export function Empty({ children }: { children: ReactNode }) { return <div className="empty">{children}</div>; }
export function DetailList({ value }: { value: unknown }) {
  if (!value) return <p className="muted">No information is available.</p>;
  if (Array.isArray(value)) return <ul>{value.map((item, i) => <li key={i}><DetailList value={item} /></li>)}</ul>;
  if (typeof value === "object") return <dl>{Object.entries(value as Record<string, unknown>).map(([key, item]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{typeof item === "object" ? <DetailList value={item} /> : String(item ?? "unknown")}</dd></div>)}</dl>;
  return <>{String(value)}</>;
}
