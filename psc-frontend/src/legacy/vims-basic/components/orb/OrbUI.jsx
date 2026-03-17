// Lightweight UI wrappers for orb-theme
import React from "react";


export function Panel({ title, right = null, fullscreen = false, children }) {
  return (
    <div className={`panel ${fullscreen ? "fullscreen" : ""}`}>
      <div className="titlebar">
        <div className="left">
          <span className="badge" />
          <h2>{title}</h2>
        </div>
        {right}
      </div>
      <div className="panel-body">{children}</div>
    </div>
  );
}


export function Card({ title, children, actions = null }) {
  return (
    <div className="card">
      {title ? <h2>{title}</h2> : null}
      {children}
      {actions}
    </div>
  );
}

export function Button({ variant = "primary", glow = false, className = "", ...props }) {
  const cls = [
    variant === "secondary" ? "btn-secondary" : "btn-primary",
    glow ? "btn-glow" : "",
    className,
  ].join(" ").trim();
  return <button className={cls} {...props} />;
}

export function Tabs({ value, items, onChange }) {
  return (
    <div className="tabs">
      {items.map((it) => (
        <button
          key={it.value}
          type="button"
          className={`tab ${value === it.value ? "active" : ""}`}
          onClick={() => onChange?.(it.value)}
        >
          {it.label}
        </button>
      ))}
    </div>
  );
}

export function Stack({ className = "", ...props }) {
  return <div className={`stack ${className}`.trim()} {...props} />;
}
