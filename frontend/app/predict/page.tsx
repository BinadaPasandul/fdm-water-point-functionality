"use client";

import { useEffect, useMemo, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, ArrowRight, CheckCircle2, LoaderCircle, MapPin, Settings2, Users, WalletCards, CloudSun } from "lucide-react";
import { useForm } from "react-hook-form";
import type { Resolver, UseFormRegister } from "react-hook-form";
import { z } from "zod";
import { Card, ErrorPanel, PageHeading, SkeletonGrid } from "@/components/ui";
import { classColors, getInputSchema, predictWaterPoint } from "@/lib/api";
import type { Field, InputSchema, Prediction } from "@/lib/types";

const groups = [
  { title: "Location", description: "Where the water point is recorded.", icon: MapPin, names: ["country","admin1","latitude_wp","longitude_wp","elevation_wp"] },
  { title: "Infrastructure", description: "Water point type, equipment, and rehabilitation.", icon: Settings2, names: ["wptype","pumptype","drillmethod","piped_source","piped_pump","wp_age","rehabyn","rehab_age"] },
  { title: "Usage & Demographics", description: "People served, households, and local demand.", icon: Users, names: ["qtypeople_wp","qtyhh_wp","qtyhh_c_wp","wpqty_wp","pop_1000","pumpstrokes"] },
  { title: "Management & Finance", description: "Responsibility, committee practice, and finance.", icon: WalletCards, names: ["cwfunded_wp","whomanage_wp","wc_present_wp","paytocollect_wp","lockedfullday_wp","wc_admin_index_wp","wc_finance_index_wp","wc_mgmt_index_wp","wc_maint_index_wp","wc_savings_wp"] },
  { title: "Environment", description: "Environmental conditions associated with the site.", icon: CloudSun, names: ["annual_rain","season","improved_wponly_wp"] },
];

function buildValidation(fields: Field[]) {
  return z.object(Object.fromEntries(fields.map((field) => [field.name,
    field.type === "number"
      ? z.string().refine((value) => value.trim() === "" || Number.isFinite(Number(value)), "Enter a valid finite number.").optional()
      : z.string().optional(),
  ])));
}

function FieldControl({ field, register, error }: { field: Field; register: UseFormRegister<Record<string, string>>; error?: string }) {
  return <div className="form-field"><label htmlFor={field.name}>{field.label}</label>
    {field.type === "number" ? <input id={field.name} type="number" step="any" inputMode="decimal" placeholder="Unknown / not available" aria-invalid={!!error} aria-describedby={error ? `${field.name}-error` : undefined} {...register(field.name)} /> : <input id={field.name} type="text" placeholder="Unknown / not available" aria-invalid={!!error} aria-describedby={error ? `${field.name}-error` : undefined} {...register(field.name)} />}
    {error && <small id={`${field.name}-error`} className="field-error">{error}</small>}
  </div>;
}

export default function PredictPage() {
  const [schema, setSchema] = useState<InputSchema | null>(null);
  const [loadError, setLoadError] = useState(""); const [loadingSchema, setLoadingSchema] = useState(true);
  const [prediction, setPrediction] = useState<Prediction | null>(null); const [submitError, setSubmitError] = useState(""); const [step, setStep] = useState(0);
  async function loadSchema() { setLoadingSchema(true); try { setSchema(await getInputSchema()); setLoadError(""); } catch (e) { setLoadError(e instanceof Error ? e.message : "The input schema is unavailable."); } finally { setLoadingSchema(false); } }
  useEffect(() => { getInputSchema().then(setSchema).catch((e: unknown) => setLoadError(e instanceof Error ? e.message : "The input schema is unavailable.")).finally(() => setLoadingSchema(false)); }, []);
  const validation = useMemo(() => buildValidation(schema?.fields ?? []), [schema]);
  const defaults = useMemo(() => Object.fromEntries((schema?.fields ?? []).map((field) => [field.name, ""])), [schema]);
  const { register, handleSubmit, trigger, getValues, formState: { errors, isSubmitting }, reset } = useForm<Record<string, string>>({ resolver: zodResolver(validation) as Resolver<Record<string, string>>, defaultValues: defaults, shouldUnregister: false });
  useEffect(() => { if (schema) reset(Object.fromEntries(schema.fields.map((field) => [field.name, ""]))); }, [schema, reset]);
  const assigned = new Set(groups.flatMap((group) => group.names));
  const extra = schema?.fields.filter((field) => !assigned.has(field.name)) ?? [];
  const steps = groups.map((group) => ({ ...group, names: [...group.names, ...extra.map((field) => field.name).filter((name) => group.title === "Environment" && !group.names.includes(name))] }));
  const active = steps[step];
  const submit = handleSubmit(async (values) => {
    setSubmitError(""); setPrediction(null);
    const payload = Object.fromEntries(schema!.fields.map((field) => {
      const raw = values[field.name] ?? "";
      return [field.name, raw.trim() === "" ? null : field.type === "number" ? Number(raw) : raw.trim()];
    }));
    try { setPrediction(await predictWaterPoint(payload)); } catch (e) { setSubmitError(e instanceof Error ? e.message : "We couldn't generate a prediction. Check the entered values and try again."); }
  });
  async function goNext() {
    if (step < groups.length - 1) {
      const names = groups[step].names.concat(step === groups.length - 1 ? extra.map((field) => field.name) : []);
      const valid = await trigger(names as never[]);
      if (valid) setStep((value) => value + 1);
    }
  }
  if (loadingSchema) return <><PageHeading eyebrow="Prediction workspace" title="Predict Water Point Functionality" description="Enter known characteristics of a water point to estimate its functionality status." /><SkeletonGrid /></>;
  if (!schema) return <><PageHeading eyebrow="Prediction workspace" title="Predict Water Point Functionality" description="Enter known characteristics of a water point to estimate its functionality status." /><ErrorPanel message={loadError} retry={() => void loadSchema()} /></>;
  const fieldByName = new Map(schema.fields.map((field) => [field.name, field]));
  return <div className="page-enter"><PageHeading eyebrow="Prediction workspace" title="Predict Water Point Functionality" description="Enter the known characteristics of a water point to estimate its current functionality status." />
    <div className="predict-layout"><form className="predict-form" onSubmit={submit} noValidate>
      <div className="form-intro"><div><b>{schema.field_count} production inputs</b><span> · Values stay saved as you move between steps</span></div><span className="pill-note">Unknown values can be left blank</span></div>
      <nav className="form-stepper" aria-label="Prediction form progress">
        <div className="stepper-desktop">{groups.map((group, index) => <div key={group.title} className={`stepper-item ${index === step ? "current" : index < step ? "complete" : ""}`} aria-current={index === step ? "step" : undefined}><span>{index < step ? "✓" : index + 1}</span><b>{group.title.replace(" & Demographics", "").replace(" & Finance", "")}</b></div>)}</div>
        <div className="stepper-mobile"><b>Step {step + 1} of 5</b><span>{active.title}</span><div className="stepper-track"><i style={{ width: `${((step + 1) / groups.length) * 100}%` }} /></div></div>
      </nav>
      <Card title={step === groups.length - 1 ? "Environment & Review" : active.title} subtitle={step === groups.length - 1 ? "Check the sections before running the prediction." : active.description} className="form-section step-card">
        <div className="fields-grid">{active.names.map((name) => fieldByName.get(name)).filter((field): field is Field => !!field).map((field) => <FieldControl key={field.name} field={field} register={register} error={errors[field.name]?.message as string | undefined} />)}</div>
        {step === groups.length - 1 && <div className="review-list">{groups.map((group, index) => { const values = getValues(); const names = group.names.concat(index === groups.length - 1 ? extra.map((field) => field.name) : []); const known = names.filter((name) => String(values[name] ?? "").trim() !== "").length; return <div key={group.title}><span><b>{group.title}</b><small>{known} of {names.length} provided · remaining values will be sent as unknown</small></span><button type="button" className="text-link review-edit" onClick={() => setStep(index)}>Edit</button></div>; })}</div>}
      </Card>
      <p className="form-note">Unknown values may be left blank. New categorical values can still be processed by the model.</p>
      <div className="step-actions">{step > 0 && <button type="button" className="button secondary" onClick={() => setStep((value) => value - 1)}><ArrowLeft size={16} /> Back</button>}{step < groups.length - 1 ? <button type="button" className="button step-next" onClick={() => void goNext()}>Next <ArrowRight size={16} /></button> : <button className="button submit-button" type="submit" disabled={isSubmitting}>{isSubmitting ? <><LoaderCircle className="spinner" size={17} />Analyzing Water Point...</> : <>Predict Functionality <ArrowRight size={16} /></>}</button>}</div>
      {submitError && <div className="error-panel" role="alert"><span><b>We couldn&apos;t generate a prediction.</b><p>{submitError}</p></span></div>}
    </form>
    <aside className="result-column" aria-live="polite">{isSubmitting && <Card title="Prediction result" subtitle="Running the production model"><div className="result-loading"><div className="skeleton result-skeleton" /><div className="skeleton result-skeleton short" /><div className="skeleton result-skeleton" /></div></Card>}
      {prediction && <Card title="Prediction result" subtitle={`Model version ${prediction.model_version}`} className="result-card"><div className="result-success"><CheckCircle2 size={18} /><span>Prediction complete</span></div><div className="predicted-label">{prediction.prediction.label}</div><div className="model-probability"><span>Model probability</span><strong>{(prediction.prediction.confidence * 100).toFixed(1)}%</strong></div><div className="probability-list"><h3>Probability distribution</h3>{Object.entries(prediction.probabilities).map(([label, value]) => <div className="probability-item" key={label}><div className="probability-caption"><span><i style={{ backgroundColor: classColors[label] ?? "var(--blue-600)" }} />{label}</span><b>{(value * 100).toFixed(1)}%</b></div><div className="probability-track"><span style={{ width: `${Math.max(0, Math.min(100, value * 100))}%`, backgroundColor: classColors[label] ?? "var(--blue-600)" }} /></div></div>)}</div><p className="disclaimer">This result is a machine-learning prediction intended to support prioritisation and field assessment. It should not replace on-site inspection.</p></Card>}
      {!prediction && !isSubmitting && <Card title="Prediction result" subtitle="Your result will appear here"><div className="empty-result"><span className="empty-result-icon"><CheckCircle2 size={22} /></span><p>Complete the steps using the information you know, then run a prediction.</p><small>Unknown values can be passed as null.</small></div></Card>}
    </aside></div>
  </div>;
}
