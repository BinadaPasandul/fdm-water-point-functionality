"use client";

import { useEffect, useMemo, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, CheckCircle2, LoaderCircle, MapPin, Settings2, Users, WalletCards, CloudSun } from "lucide-react";
import { useForm } from "react-hook-form";
import type { Resolver, UseFormRegister } from "react-hook-form";
import { z } from "zod";
import { Card, ErrorPanel, PageHeading, SkeletonGrid } from "@/components/ui";
import { classColors, getInputSchema, predictWaterPoint } from "@/lib/api";
import type { Field, InputSchema, Prediction } from "@/lib/types";

const groups = [
  { title: "Location", description: "Where the water point is recorded.", icon: MapPin, names: ["country","admin1","latitude_wp","longitude_wp","elevation_wp"] },
  { title: "Infrastructure", description: "Water point type, equipment, and rehabilitation.", icon: Settings2, names: ["wptype","pumptype","drillmethod","piped_source","piped_pump","wp_age","rehabyn","rehab_age"] },
  { title: "Usage & demographics", description: "People, households, and local demand measures.", icon: Users, names: ["qtypeople_wp","qtyhh_wp","qtyhh_c_wp","wpqty_wp","pop_1000","pumpstrokes"] },
  { title: "Management & finance", description: "Responsibility, committee practice, and finance indicators.", icon: WalletCards, names: ["whomanage_wp","cwfunded_wp","wc_present_wp","paytocollect_wp","lockedfullday_wp","wc_admin_index_wp","wc_finance_index_wp","wc_mgmt_index_wp","wc_maint_index_wp","wc_savings_wp"] },
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
  return <div className="form-field"><label htmlFor={field.name}>{field.label}<span className="field-optional"> · may be unknown</span></label>
    {field.type === "number" ? <input id={field.name} type="number" step="any" inputMode="decimal" placeholder="Unknown / not available" aria-invalid={!!error} aria-describedby={error ? `${field.name}-error` : `${field.name}-hint`} {...register(field.name)} /> : <input id={field.name} type="text" list={`${field.name}-suggestions`} placeholder="Unknown / not available" aria-invalid={!!error} aria-describedby={error ? `${field.name}-error` : `${field.name}-hint`} {...register(field.name)} />}
    {field.type === "categorical" && <datalist id={`${field.name}-suggestions`}><option value="Unknown" /><option value="Not applicable" /></datalist>}
    <small id={error ? `${field.name}-error` : `${field.name}-hint`} className={error ? "field-error" : "field-hint"}>{error || field.description || (field.nullable ? "Leave blank to send null." : "Required field.")}</small>
  </div>;
}

export default function PredictPage() {
  const [schema, setSchema] = useState<InputSchema | null>(null);
  const [loadError, setLoadError] = useState(""); const [loadingSchema, setLoadingSchema] = useState(true);
  const [prediction, setPrediction] = useState<Prediction | null>(null); const [submitError, setSubmitError] = useState("");
  async function loadSchema() { setLoadingSchema(true); try { setSchema(await getInputSchema()); setLoadError(""); } catch (e) { setLoadError(e instanceof Error ? e.message : "The input schema is unavailable."); } finally { setLoadingSchema(false); } }
  useEffect(() => { getInputSchema().then(setSchema).catch((e: unknown) => setLoadError(e instanceof Error ? e.message : "The input schema is unavailable.")).finally(() => setLoadingSchema(false)); }, []);
  const validation = useMemo(() => buildValidation(schema?.fields ?? []), [schema]);
  const defaults = useMemo(() => Object.fromEntries((schema?.fields ?? []).map((field) => [field.name, ""])), [schema]);
  const { register, handleSubmit, formState: { errors, isSubmitting }, reset } = useForm<Record<string, string>>({ resolver: zodResolver(validation) as Resolver<Record<string, string>>, defaultValues: defaults });
  useEffect(() => { if (schema) reset(Object.fromEntries(schema.fields.map((field) => [field.name, ""]))); }, [schema, reset]);
  const submit = handleSubmit(async (values) => {
    setSubmitError(""); setPrediction(null);
    const payload = Object.fromEntries(schema!.fields.map((field) => {
      const raw = values[field.name] ?? "";
      return [field.name, raw.trim() === "" ? null : field.type === "number" ? Number(raw) : raw.trim()];
    }));
    try { setPrediction(await predictWaterPoint(payload)); } catch (e) { setSubmitError(e instanceof Error ? e.message : "We couldn't generate a prediction. Check the entered values and try again."); }
  });
  if (loadingSchema) return <><PageHeading eyebrow="Prediction workspace" title="Predict Water Point Functionality" description="Enter known characteristics of a water point to estimate its functionality status." /><SkeletonGrid /></>;
  if (!schema) return <><PageHeading eyebrow="Prediction workspace" title="Predict Water Point Functionality" description="Enter known characteristics of a water point to estimate its functionality status." /><ErrorPanel message={loadError} retry={() => void loadSchema()} /></>;
  const assigned = new Set(groups.flatMap((group) => group.names));
  const extra = schema.fields.filter((field) => !assigned.has(field.name));
  return <div className="page-enter"><PageHeading eyebrow="Prediction workspace" title="Predict Water Point Functionality" description="Enter the known characteristics of a water point to estimate its current functionality status." />
    <div className="predict-layout"><form className="predict-form" onSubmit={submit} noValidate>
      <div className="form-intro"><div><b>{schema.field_count} input fields</b><span> · All are part of the API contract</span></div><span className="pill-note">Unknown values can be left blank</span></div>
      <div className="form-sections">{groups.map((group) => { const GroupIcon = group.icon; const fields = group.names.map((name) => schema.fields.find((field) => field.name === name)).filter((field): field is Field => !!field); return <Card key={group.title} title={group.title} subtitle={group.description} className="form-section"><div className="section-icon"><GroupIcon size={17} /></div><div className="fields-grid">{fields.map((field) => <FieldControl key={field.name} field={field} register={register} error={errors[field.name]?.message as string | undefined} />)}</div></Card>; })}
        {extra.length > 0 && <Card title="Other inputs" subtitle="Remaining fields provided by the API schema" className="form-section"><div className="fields-grid">{extra.map((field) => <FieldControl key={field.name} field={field} register={register} error={errors[field.name]?.message as string | undefined} />)}</div></Card>}
      </div>
      <p className="form-note">Blank values are sent as JSON <code>null</code>. Unseen categorical values are accepted by the backend model pipeline.</p>
      <button className="button full submit-button" type="submit" disabled={isSubmitting}>{isSubmitting ? <><LoaderCircle className="spinner" size={17} />Analyzing Water Point...</> : <>Predict Functionality <ArrowRight size={16} /></>}</button>
      {submitError && <div className="error-panel" role="alert"><span><b>We couldn&apos;t generate a prediction.</b><p>{submitError}</p></span></div>}
    </form>
    <aside className="result-column" aria-live="polite">{isSubmitting && <Card title="Prediction result" subtitle="Running the production model"><div className="result-loading"><div className="skeleton result-skeleton" /><div className="skeleton result-skeleton short" /><div className="skeleton result-skeleton" /></div></Card>}
      {prediction && <Card title="Prediction result" subtitle={`Model version ${prediction.model_version}`} className="result-card"><div className="result-success"><CheckCircle2 size={18} /><span>Prediction complete</span></div><div className="predicted-label" style={{ color: classColors[prediction.prediction.label] ?? "var(--navy-800)" }}>{prediction.prediction.label}</div><div className="model-probability"><span>Model probability</span><strong>{(prediction.prediction.confidence * 100).toFixed(1)}%</strong></div><div className="probability-list"><h3>Probability distribution</h3>{Object.entries(prediction.probabilities).map(([label, value]) => <div className="probability-item" key={label}><div className="probability-caption"><span><i style={{ backgroundColor: classColors[label] ?? "#4D728F" }} />{label}</span><b>{(value * 100).toFixed(1)}%</b></div><div className="probability-track"><span style={{ width: `${Math.max(0, Math.min(100, value * 100))}%`, backgroundColor: classColors[label] ?? "#4D728F" }} /></div></div>)}</div><p className="disclaimer">This result is a machine-learning prediction intended to support prioritisation and field assessment. It should not replace on-site inspection.</p></Card>}
      {!prediction && !isSubmitting && <Card title="Prediction result" subtitle="Your result will appear here"><div className="empty-result"><span className="empty-result-icon"><CheckCircle2 size={22} /></span><p>Complete the fields you know, then run a prediction.</p><small>Every blank field will be passed to the backend as null.</small></div></Card>}
    </aside></div>
  </div>;
}
