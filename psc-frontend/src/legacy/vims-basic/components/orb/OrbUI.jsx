import React from "react";
import {
  Card as SharedCard,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button as SharedButton } from "@/components/ui/button";

export function Panel({ title, right = null, fullscreen = false, children }) {
  return (
    <section className={`panel ${fullscreen ? "fullscreen" : ""}`}>
      <div className="titlebar">
        <div className="left">
          <span className="badge" />
          <h2>{title}</h2>
        </div>
        {right ? <div>{right}</div> : null}
      </div>
      <div className="panel-body">{children}</div>
    </section>
  );
}

export function Card({ title, children, actions = null, className = "" }) {
  return (
    <SharedCard className={`orb-card ${className}`.trim()}>
      {title ? (
        <CardHeader className="p-card-title">
          <div className="flex items-start justify-between gap-3">
            <CardTitle className="font-semibold mb-3">{title}</CardTitle>
            {actions ? <div className="shrink-0">{actions}</div> : null}
          </div>
        </CardHeader>
      ) : null}
      <CardContent className="p-card-content">{children}</CardContent>
    </SharedCard>
  );
}

export function Button({
  variant = "primary",
  glow = false,
  className = "",
  children,
  ...props
}) {
  const mappedVariant =
    variant === "secondary"
      ? "secondary"
      : variant === "ghost"
        ? "ghost"
        : variant === "outline"
          ? "outline"
          : "default";

  return (
    <SharedButton
      variant={mappedVariant}
      className={[glow ? "orb-btn-glow" : "", className].join(" ").trim()}
      {...props}
    >
      {children}
    </SharedButton>
  );
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
