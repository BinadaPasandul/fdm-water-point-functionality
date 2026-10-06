"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, Search } from "lucide-react";
import type { FieldOption } from "@/lib/types";

const unknownOption: FieldOption = { label: "Unknown / not available", value: "" };

type SelectProps = {
  id: string;
  label: string;
  value: string;
  options: FieldOption[];
  onChange: (value: string) => void;
  error?: string;
  searchable?: boolean;
  disabled?: boolean;
};

export function SelectField({ id, label, value, options, onChange, error, disabled }: SelectProps) {
  return <div className="form-field">
    <label htmlFor={id}>{label}</label>
    <div className="select-shell">
      <select id={id} value={value} disabled={disabled} aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : undefined}
        onChange={(event) => onChange(event.target.value)}>
        <option value="">{unknownOption.label}</option>
        {options.map((option) => <option key={`${option.label}:${option.value}`} value={String(option.value)}>{option.label}</option>)}
      </select>
      <ChevronDown className="select-chevron" size={17} aria-hidden="true" />
    </div>
    {error && <small id={`${id}-error`} className="field-error">{error}</small>}
  </div>;
}

export function SearchableSelectField({ id, label, value, options, onChange, error, disabled }: SelectProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const selected = options.find((option) => String(option.value) === value);
  const filtered = useMemo(() => options.filter((option) => option.label.toLocaleLowerCase().includes(query.toLocaleLowerCase())), [options, query]);
  useEffect(() => {
    function onOutside(event: MouseEvent) {
      if (!root.current?.contains(event.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("mousedown", onOutside);
    return () => document.removeEventListener("mousedown", onOutside);
  }, []);

  function choose(option: FieldOption) {
    onChange(String(option.value));
    setOpen(false);
    setQuery("");
  }
  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") { setOpen(false); setQuery(""); return; }
    if (event.key === "ArrowDown") { event.preventDefault(); setOpen(true); setActiveIndex((index) => Math.min(index + 1, filtered.length - 1)); }
    if (event.key === "ArrowUp") { event.preventDefault(); setOpen(true); setActiveIndex((index) => Math.max(index - 1, 0)); }
    if (event.key === "Enter" && open) {
      event.preventDefault();
      if (filtered[activeIndex]) choose(filtered[activeIndex]);
    }
  }

  return <div className="form-field">
    <label id={`${id}-label`} htmlFor={id}>{label}</label>
    <div ref={root} className={`search-select ${open ? "is-open" : ""}`}>
      <Search size={16} aria-hidden="true" className="search-select-icon" />
      <input id={id} role="combobox" aria-labelledby={`${id}-label`} aria-autocomplete="list"
        aria-expanded={open} aria-controls={`${id}-options`} aria-activedescendant={open && filtered[activeIndex] ? `${id}-option-${activeIndex}` : undefined}
        aria-invalid={!!error} aria-describedby={error ? `${id}-error` : undefined}
        autoComplete="off" disabled={disabled} placeholder={unknownOption.label}
        value={open ? query : selected?.label ?? ""}
        onFocus={() => { if (!disabled) setOpen(true); }}
        onClick={() => setOpen(true)}
        onChange={(event) => { setQuery(event.target.value); setOpen(true); setActiveIndex(0); if (event.target.value === "") onChange(""); }}
        onKeyDown={onKeyDown} />
      <button type="button" className="search-select-toggle" aria-label={`Show ${label} options`} tabIndex={-1} onClick={() => setOpen((state) => !state)}><ChevronDown size={17} aria-hidden="true" /></button>
      {open && <div className="search-select-menu" id={`${id}-options`} role="listbox" aria-labelledby={`${id}-label`}>
        <button type="button" className={`search-select-option unknown-option ${value === "" ? "selected" : ""}`} role="option" aria-selected={value === ""} onMouseDown={(event) => event.preventDefault()} onClick={() => choose(unknownOption)}>{unknownOption.label}</button>
        {filtered.map((option, index) => <button type="button" id={`${id}-option-${index}`} key={`${option.label}:${option.value}`} className={`search-select-option ${String(option.value) === value ? "selected" : ""} ${activeIndex === index ? "active" : ""}`} role="option" aria-selected={String(option.value) === value} onMouseDown={(event) => event.preventDefault()} onClick={() => choose(option)}>{option.label}</button>)}
        {filtered.length === 0 && <p className="search-select-empty">No matching known categories.</p>}
      </div>}
    </div>
    {error && <small id={`${id}-error`} className="field-error">{error}</small>}
  </div>;
}
