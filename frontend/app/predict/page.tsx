"use client";

import { useEffect, useMemo, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, ArrowRight, CheckCircle2, LoaderCircle, MapPin, Settings2, Users, WalletCards, CloudSun } from "lucide-react";
import { Controller, useForm, useWatch } from "react-hook-form";
import type { Resolver } from "react-hook-form";
import { z } from "zod";
import { Card, ErrorPanel, PageHeading, SkeletonGrid } from "@/components/ui";
import { SearchableSelectField, SelectField } from "@/components/prediction-fields";
import { classColors, getInputSchema, predictWaterPoint } from "@/lib/api";
import type { Field, InputSchema, Prediction } from "@/lib/types";

type FormValues = Record<string, string>;
type PredictionPayload = Record<string, string | number | null>;
const groups = [
  { title: "Location", description: "Where the water point is recorded.", icon: MapPin, names: ["country", "admin1", "latitude_wp", "longitude_wp", "elevation_wp"] },
  { title: "Infrastructure", description: "Water point type, equipment, and rehabilitation.", icon: Settings2, names: ["wptype", "pumptype", "drillmethod", "piped_source", "piped_pump", "wp_age", "rehabyn", "rehab_age"] },
  { title: "Usage & Demographics", description: "People served, households, and local demand.", icon: Users, names: ["qtypeople_wp", "qtyhh_wp", "qtyhh_c_wp", "wpqty_wp", "pop_1000", "pumpstrokes"] },
  { title: "Management & Finance", description: "Responsibility, committee practice, and finance.", icon: WalletCards, names: ["cwfunded_wp", "whomanage_wp", "wc_present_wp", "paytocollect_wp", "lockedfullday_wp", "wc_admin_index_wp", "wc_finance_index_wp", "wc_mgmt_index_wp", "wc_maint_index_wp", "wc_savings_wp"] },
  { title: "Environment", description: "Environmental conditions associated with the site.", icon: CloudSun, names: ["annual_rain", "season", "improved_wponly_wp"] },
];
const compatiblePumpTypes = new Set(["Borehole with hand pump", "Protected dug well with hand pump", "Unprotected dug well"]);
const compatibleDrillTypes = new Set(["Borehole with hand pump", "Mechanized borehole", "Protected dug well with hand pump", "Unprotected dug well"]);
const compatiblePipedTypes = new Set(["Mechanized borehole", "Piped water into yard / plot", "Public tap / standpipe"]);
const committeeFields = ["wc_admin_index_wp", "wc_finance_index_wp", "wc_mgmt_index_wp", "wc_maint_index_wp", "wc_savings_wp"];

function buildValidation(fields: Field[]) {
  return z.object(Object.fromEntries(fields.map((field) => [field.name,
    field.type === "number"
      ? z.string().refine((value) => value.trim() === "" || Number.isFinite(Number(value)), "Enter a valid finite number.").optional()
      : z.string().optional(),
  ])));
}

function toPayload(fields: Field[], values: FormValues): PredictionPayload {
  return Object.fromEntries(fields.map((field) => {
    const raw = values[field.name] ?? "";
    if (raw.trim() === "") return [field.name, null];
    if (field.type === "number" || field.type === "binary_numeric") return [field.name, Number(raw)];
    return [field.name, raw];
  }));
}

function isApplicable(name: string, values: FormValues) {
  if (name === "rehab_age") return values.rehabyn === "Yes";
  if (name === "pumptype") return compatiblePumpTypes.has(values.wptype ?? "");
  if (name === "drillmethod") return compatibleDrillTypes.has(values.wptype ?? "");
  if (name === "piped_source" || name === "piped_pump") return compatiblePipedTypes.has(values.wptype ?? "");
  if (committeeFields.includes(name)) return values.wc_present_wp === "Yes";
  return true;
}

export default function PredictPage() {
  const [schema, setSchema] = useState<InputSchema | null>(null);
  const [loadError, setLoadError] = useState("");
  const [loadingSchema, setLoadingSchema] = useState(true);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [submittedSnapshot, setSubmittedSnapshot] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState("");
  const [step, setStep] = useState(0);

  async function loadSchema() {
    setLoadingSchema(true);
    try { setSchema(await getInputSchema()); setLoadError(""); }
    catch (error) { setLoadError(error instanceof Error ? error.message : "The input schema is unavailable."); }
    finally { setLoadingSchema(false); }
  }
  useEffect(() => { void loadSchema(); }, []);

  const validation = useMemo(() => buildValidation(schema?.fields ?? []), [schema]);
  const defaults = useMemo(() => Object.fromEntries((schema?.fields ?? []).map((field) => [field.name, ""])), [schema]);
  const { control, handleSubmit, trigger, getValues, setValue, formState: { errors, isSubmitting }, reset } = useForm<FormValues>({
    resolver: zodResolver(validation) as Resolver<FormValues>, defaultValues: defaults, shouldUnregister: false,
  });
  const watched = useWatch({ control });
  const values = (watched ?? {}) as FormValues;
  const currentPayload = useMemo(() => schema ? toPayload(schema.fields, values) : {}, [schema, values]);
  const currentSnapshot = JSON.stringify(currentPayload);

  useEffect(() => { if (schema) reset(Object.fromEntries(schema.fields.map((field) => [field.name, ""]))); }, [schema, reset]);

  useEffect(() => {
    if (!schema) return;
    const clearIfHidden = (name: string) => {
      if (!isApplicable(name, values) && values[name] !== "") setValue(name, "", { shouldDirty: true, shouldValidate: true });
    };
    ["rehab_age", "pumptype", "drillmethod", "piped_source", "piped_pump", ...committeeFields].forEach(clearIfHidden);
  }, [schema, values, setValue]);

  const fieldByName = useMemo(() => new Map((schema?.fields ?? []).map((field) => [field.name, field])), [schema]);
  const stepFields = groups[step].names.map((name) => fieldByName.get(name)).filter((field): field is Field => !!field);
  const resultIsStale = prediction !== null && submittedSnapshot !== null && currentSnapshot !== submittedSnapshot;

  const submit = handleSubmit(async (formValues) => {
    if (!schema) return;
    setSubmitError("");
    setPrediction(null);
    const payload = toPayload(schema.fields, formValues);
    const snapshot = JSON.stringify(payload);
    try {
      const result = await predictWaterPoint(payload);
      setPrediction(result);
      setSubmittedSnapshot(snapshot);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "We couldn't generate a prediction. Check the entered values and try again.");
    }
  });

  async function goNext() {
    if (step >= groups.length - 1) return;
    const valid = await trigger(groups[step].names as never[]);
    if (valid) setStep((current) => current + 1);
  }

  function changeCountry(country: string) {
    const region = values.admin1 ?? "";
    const regionField = fieldByName.get("admin1");
    const compatible = country ? regionField?.options_by_parent?.[country] ?? [] : regionField?.known_options ?? [];
    setValue("country", country, { shouldDirty: true, shouldValidate: true });
    if (region && !compatible.some((option) => String(option.value) === region)) {
      setValue("admin1", "", { shouldDirty: true, shouldValidate: true });
    }
  }

  if (loadingSchema) return <><PageHeading eyebrow="Prediction workspace" title="Predict Water Point Functionality" description="Enter known characteristics of a water point to estimate its functionality status." /><SkeletonGrid /></>;
  if (!schema) return <><PageHeading eyebrow="Prediction workspace" title="Predict Water Point Functionality" description="Enter known characteristics of a water point to estimate its functionality status." /><ErrorPanel message={loadError} retry={() => void loadSchema()} /></>;

  return <div className="page-enter">
    <PageHeading eyebrow="Prediction workspace" title="Predict Water Point Functionality" description="Enter the known characteristics of a water point to estimate its current functionality status." />
    <div className="predict-layout"><form className="predict-form" onSubmit={submit} noValidate>
      <div className="form-intro"><div><b>{schema.field_count} water point details</b><span> · Values stay saved as you move between steps</span></div><span className="pill-note">Unknown values can be left blank</span></div>
      <nav className="form-stepper" aria-label="Prediction form progress">
        <div className="stepper-desktop">{groups.map((group, index) => <div key={group.title} className={`stepper-item ${index === step ? "current" : index < step ? "complete" : ""}`} aria-current={index === step ? "step" : undefined}><span>{index < step ? "✓" : index + 1}</span><b>{group.title.replace(" & Demographics", "").replace(" & Finance", "")}</b></div>)}</div>
        <div className="stepper-mobile"><b>Step {step + 1} of 5</b><span>{groups[step].title}</span><div className="stepper-track"><i style={{ width: `${((step + 1) / groups.length) * 100}%` }} /></div></div>
      </nav>
      <Card title={step === groups.length - 1 ? "Environment & Review" : groups[step].title} subtitle={step === groups.length - 1 ? "Check the sections before running the prediction." : groups[step].description} className="form-section step-card">
        <div className="fields-grid">{stepFields.filter((field) => isApplicable(field.name, values)).map((field) => {
          const error = errors[field.name]?.message as string | undefined;
          const isSearchable = ["country", "admin1", "wptype", "whomanage_wp"].includes(field.name);
          let options = field.known_options ?? [];
          if (field.name === "admin1" && values.country) options = field.options_by_parent?.[values.country] ?? [];
          return <Controller key={field.name} name={field.name} control={control} render={({ field: controlField }) => field.type === "number"
            ? <div className="form-field"><label htmlFor={field.name}>{field.label}</label><input id={field.name} type="number" step="any" inputMode="decimal" placeholder="Unknown / not available" aria-invalid={!!error} aria-describedby={error ? `${field.name}-error` : undefined} value={controlField.value ?? ""} onChange={controlField.onChange} onBlur={controlField.onBlur} name={controlField.name} ref={controlField.ref} />{error && <small id={`${field.name}-error`} className="field-error">{error}</small>}</div>
            : isSearchable
              ? <SearchableSelectField id={field.name} label={field.label} value={controlField.value ?? ""} options={options} error={error} onChange={field.name === "country" ? changeCountry : controlField.onChange} />
              : <SelectField id={field.name} label={field.label} value={controlField.value ?? ""} options={options} error={error} onChange={controlField.onChange} />} />;
        })}</div>
        {step === groups.length - 1 && <div className="review-list">{groups.map((group) => {
          const names = group.names.filter((name) => fieldByName.has(name));
          const applicable = names.filter((name) => isApplicable(name, values));
          const provided = applicable.filter((name) => String(values[name] ?? "").trim() !== "").length;
          const notApplicable = names.length - applicable.length;
          const unknown = applicable.length - provided;
          const counts = [`${provided} provided`, `${unknown} unknown`];
          if (notApplicable) counts.push(`${notApplicable} not applicable`);
          return <div key={group.title}><span><b>{group.title}</b><small>{counts.join(" · ")}</small></span><button type="button" className="text-link review-edit" onClick={() => setStep(groups.indexOf(group))}>Edit</button></div>;
        })}</div>}
      </Card>
      <p className="form-note">Select from known categories where available. Fields without known information may be left as Unknown.</p>
      <div className="step-actions">{step > 0 && <button type="button" className="button secondary" onClick={() => setStep((current) => current - 1)}><ArrowLeft size={16} /> Back</button>}{step < groups.length - 1 ? <button type="button" className="button step-next" onClick={() => void goNext()}>Next <ArrowRight size={16} /></button> : <button className="button submit-button" type="submit" disabled={isSubmitting}>{isSubmitting ? <><LoaderCircle className="spinner" size={17} />Analyzing Water Point...</> : <>Predict Functionality <ArrowRight size={16} /></>}</button>}</div>
      {submitError && <div className="error-panel" role="alert"><span><b>We couldn&apos;t generate a prediction.</b><p>{submitError}</p></span></div>}
    </form>
    <aside className="result-column" aria-live="polite">
      {isSubmitting && <Card title="Prediction result" subtitle="Running the production model"><div className="result-loading"><div className="skeleton result-skeleton" /><div className="skeleton result-skeleton short" /><div className="skeleton result-skeleton" /></div></Card>}
      {prediction && resultIsStale && !isSubmitting && <Card title="Prediction result" subtitle="The form has changed since this result was created"><div className="stale-result" role="status"><strong>Inputs changed</strong><p>Run the prediction again to update this result.</p></div></Card>}
      {prediction && !resultIsStale && <Card title="Prediction result" subtitle={`Model version ${prediction.model_version}`} className="result-card"><div className="result-success"><CheckCircle2 size={18} /><span>Prediction complete</span></div><div className="predicted-label">{prediction.prediction.label}</div><div className="model-probability"><span>Model probability</span><strong>{(prediction.prediction.confidence * 100).toFixed(1)}%</strong></div><div className="probability-list"><h3>Probability distribution</h3>{Object.entries(prediction.probabilities).map(([label, value]) => <div className="probability-item" key={label}><div className="probability-caption"><span><i style={{ backgroundColor: classColors[label] ?? "var(--blue-600)" }} />{label}</span><b>{(value * 100).toFixed(1)}%</b></div><div className="probability-track"><span style={{ width: `${Math.max(0, Math.min(100, value * 100))}%`, backgroundColor: classColors[label] ?? "var(--blue-600)" }} /></div></div>)}</div><p className="disclaimer">This result is a machine-learning prediction intended to support prioritisation and field assessment. It should not replace on-site inspection.</p></Card>}
      {!prediction && !isSubmitting && <Card title="Prediction result" subtitle="Your result will appear here"><div className="empty-result"><span className="empty-result-icon"><CheckCircle2 size={22} /></span><p>Complete the steps using the information you know, then run a prediction.</p><small>Unknown values can be passed as null.</small></div></Card>}
    </aside></div>
  </div>;
}
