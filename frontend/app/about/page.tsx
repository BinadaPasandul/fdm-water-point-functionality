"use client";

import Link from "next/link";
import { ArrowRight, Database, GitBranch, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Card, ErrorPanel, PageHeading } from "@/components/ui";
import { getModelInfo } from "@/lib/api";

export default function AboutPage() {
  const [model, setModel] = useState<Record<string, unknown> | null>(null); const [error, setError] = useState("");
  useEffect(() => { getModelInfo().then(setModel).catch((e: unknown) => setError(e instanceof Error ? e.message : "Model information is unavailable.")); }, []);
  return <div className="page-enter"><PageHeading eyebrow="Project overview" title="About the Model" description="A concise, viva-friendly explanation of the data flow and the role of this prediction interface." action={<Link className="button" href="/predict">Try a prediction <ArrowRight size={16} /></Link>} />
    <div className="about-hero"><div className="about-mark"><Database size={25} /></div><div><span className="eyebrow">University Data Mining Mini Project</span><h2>Predicting Rural Water Point Functionality</h2><p>This project studies whether a rural water point is functional, partially functional, or abandoned / not functional using recorded infrastructure, location, use, management, and environmental features.</p></div></div>
    {error && <ErrorPanel message={error} />}
    {model && <div className="model-overview about-model-overview"><div><span className="eyebrow">Model from API</span><h2>{String(model.model_family)}</h2><p>{String(model.preprocessing_variant)} · {String(model.raw_predictor_count)} raw predictors · {String(model.selected_feature_count)} selected features</p></div><div className="headline-score"><strong>{String(model.model_version)}</strong><span>Model version</span></div></div>}
    <div className="insight-grid about-grid"><Card title="How a prediction works" subtitle="One pipeline from submitted row to result"><ol className="steps-list"><li><span>01</span><div><b>Enter known characteristics</b><p>The form loads its 32 field definitions from the FastAPI input schema. Every field may be sent as a value or explicit JSON null.</p></div></li><li><span>02</span><div><b>FastAPI validates the request</b><p>The browser sends one JSON record to the existing versioned prediction endpoint.</p></div></li><li><span>03</span><div><b>Production pipeline predicts</b><p>The backend runs the serialized and verified Random Forest pipeline, including its fitted preprocessing.</p></div></li><li><span>04</span><div><b>Review all class scores</b><p>The response shows the predicted class and the probability values returned by the model.</p></div></li></ol></Card>
      <Card title="What to keep in mind" subtitle="Responsible interpretation"><div className="about-principles"><div><ShieldCheck /><div><b>Decision support</b><p>Use predictions to support prioritisation and field assessment, not to replace an on-site inspection.</p></div></div><div><GitBranch /><div><b>One source of truth</b><p>Inference, preprocessing, dashboard evidence, and metrics stay in the backend project services.</p></div></div></div><div className="info-callout">A model probability is not a guarantee. Data quality, class imbalance, and differences between countries can affect performance.</div></Card></div>
  </div>;
}
