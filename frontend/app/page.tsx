"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import {
  Activity, ArrowRight, Boxes, CheckCircle2, CircleAlert, Database,
  FlaskConical, Layers3, LoaderCircle, ShieldCheck, TerminalSquare,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type DatasetItem = {
  id: string;
  name: string;
  description: string | null;
  latest_version_id: string | null;
  latest_version: number | null;
  test_case_count: number;
};

type ModelItem = {
  id: string;
  name: string;
  provider: string;
  model_id: string;
  endpoint_url: string;
  api_key_env: string;
  is_enabled: boolean;
};

type ExperimentItem = {
  id: string;
  name: string;
  status: string;
  dataset_version_id: string;
  model_config_id: string;
};

type ResultItem = {
  id: string;
  test_case_id: string;
  status: string;
  model_output: string | null;
  score: number | null;
  failure_category: string | null;
  latency_ms: number | null;
  error_message: string | null;
};

type RunItem = {
  id: string;
  experiment_id: string;
  status: string;
  summary: {
    total_cases?: number;
    succeeded?: number;
    errors?: number;
    scored?: number;
    unscored?: number;
    mean_score?: number | null;
    failure_categories?: Record<string, number>;
  };
  results: ResultItem[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.detail || `Request failed with status ${response.status}`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return response.json() as Promise<T>;
}

function MetricCard({ label, value, note, icon: Icon }: {
  label: string; value: string; note: string; icon: typeof FlaskConical;
}) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between p-5">
        <div>
          <p className="text-xs font-medium text-muted-foreground">{label}</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight tabular-nums">{value}</p>
          <p className="mt-1 text-[11px] text-muted-foreground">{note}</p>
        </div>
        <div className="rounded-lg border bg-slate-50 p-2 text-slate-500"><Icon className="size-4" /></div>
      </CardContent>
    </Card>
  );
}

export default function HomePage() {
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [models, setModels] = useState<ModelItem[]>([]);
  const [experiments, setExperiments] = useState<ExperimentItem[]>([]);
  const [selectedExperiment, setSelectedExperiment] = useState("");
  const [latestRun, setLatestRun] = useState<RunItem | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [datasetName, setDatasetName] = useState("First reliability dataset");
  const [question, setQuestion] = useState("What is the capital of France?");
  const [expectedAnswer, setExpectedAnswer] = useState("Paris");

  const [modelName, setModelName] = useState("OpenAI-compatible model");
  const [modelId, setModelId] = useState("gpt-4o-mini");
  const [endpointUrl, setEndpointUrl] = useState("https://api.openai.com/v1");
  const [apiKeyEnv, setApiKeyEnv] = useState("OPENAI_API_KEY");

  const [experimentName, setExperimentName] = useState("First reliability experiment");
  const [systemPrompt, setSystemPrompt] = useState("Answer briefly and precisely.");
  const [selectedDatasetVersion, setSelectedDatasetVersion] = useState("");
  const [selectedModel, setSelectedModel] = useState("");

  const refreshData = useCallback(async () => {
    try {
      const [datasetData, modelData, experimentData] = await Promise.all([
        apiRequest<DatasetItem[]>("/datasets"),
        apiRequest<ModelItem[]>("/models"),
        apiRequest<ExperimentItem[]>("/experiments"),
      ]);
      setDatasets(datasetData);
      setModels(modelData);
      setExperiments(experimentData);
      setSelectedDatasetVersion((current) =>
        datasetData.some((item) => item.latest_version_id === current)
          ? current
          : datasetData.find((item) => item.latest_version_id)?.latest_version_id || "",
      );
      setSelectedModel((current) =>
        modelData.some((item) => item.id === current)
          ? current
          : modelData.find((item) => item.is_enabled)?.id || "",
      );
      setSelectedExperiment((current) =>
        experimentData.some((item) => item.id === current)
          ? current
          : experimentData[0]?.id || "",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load workspace data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void refreshData(), 0);
    return () => window.clearTimeout(timer);
  }, [refreshData]);

  const activeExperiment = useMemo(
    () => experiments.find((item) => item.id === selectedExperiment),
    [experiments, selectedExperiment],
  );

  async function createDataset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const created = await apiRequest<{ version_id: string }>("/datasets", {
        method: "POST",
        body: JSON.stringify({
          name: datasetName,
          description: "Created in the Reliability Lab workspace.",
          test_cases: [{
            external_id: "case-001",
            input_text: question,
            expected_output: expectedAnswer || null,
            tags: ["manual", "first-run"],
          }],
        }),
      });
      await refreshData();
      setSelectedDatasetVersion(created.version_id);
      setMessage("Dataset and immutable version 1 created.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dataset creation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function createModel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const created = await apiRequest<ModelItem>("/models", {
        method: "POST",
        body: JSON.stringify({
          name: modelName,
          provider: "openai_compatible",
          model_id: modelId,
          endpoint_url: endpointUrl,
          api_key_env: apiKeyEnv,
          parameters: { temperature: 0 },
        }),
      });
      await refreshData();
      setSelectedModel(created.id);
      setMessage("Model configuration saved. Add the corresponding API key to backend/.env.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Model configuration failed.");
    } finally {
      setBusy(false);
    }
  }

  async function createExperiment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedDatasetVersion || !selectedModel) {
      setError("Create a dataset and model configuration before creating an experiment.");
      return;
    }
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const created = await apiRequest<ExperimentItem>("/experiments", {
        method: "POST",
        body: JSON.stringify({
          name: experimentName,
          dataset_version_id: selectedDatasetVersion,
          model_config_id: selectedModel,
          system_prompt: systemPrompt || null,
          evaluator_config: { method: "normalized_exact_match" },
        }),
      });
      await refreshData();
      setSelectedExperiment(created.id);
      setLatestRun(null);
      setMessage("Experiment created with its dataset and model references.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Experiment creation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function runExperiment() {
    if (!activeExperiment) return;
    setBusy(true);
    setError("");
    setMessage("");
    setLatestRun(null);
    try {
      const run = await apiRequest<{ id: string }>(`/experiments/${activeExperiment.id}/runs`, {
        method: "POST",
      });
      const detail = await apiRequest<RunItem>(`/runs/${run.id}`);
      setLatestRun(detail);
      setMessage("Evaluation run finished and results were retrieved from the API.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation run failed.");
    } finally {
      setBusy(false);
      await refreshData();
    }
  }

  const meanScore = latestRun?.summary.mean_score;
  const meanScoreText = typeof meanScore === "number" ? `${(meanScore * 100).toFixed(1)}%` : "—";

  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col border-r bg-white xl:flex">
        <div className="flex h-16 items-center gap-3 border-b px-5">
          <div className="flex size-8 items-center justify-center rounded-lg bg-blue-600 text-white"><Activity className="size-4" /></div>
          <div><p className="text-sm font-semibold tracking-tight">Reliability Lab</p><p className="text-[10px] text-muted-foreground">Research workspace</p></div>
        </div>
        <div className="px-3 py-5">
          <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Workspace</p>
          <nav className="space-y-1 text-sm">
            <a className="flex items-center gap-3 rounded-lg bg-blue-50 px-3 py-2 font-medium text-blue-700" href="#overview"><Activity className="size-4" /> Overview</a>
            <a className="flex items-center gap-3 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-50" href="#datasets"><Layers3 className="size-4" /> Datasets</a>
            <a className="flex items-center gap-3 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-50" href="#models"><Boxes className="size-4" /> Models</a>
            <a className="flex items-center gap-3 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-50" href="#experiments"><FlaskConical className="size-4" /> Experiments</a>
            <a className="flex items-center gap-3 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-50" href="#latest-run"><ShieldCheck className="size-4" /> Latest run</a>
          </nav>
        </div>
        <div className="mt-auto border-t p-4">
          <div className="rounded-lg bg-slate-50 p-3"><p className="text-xs font-medium">Local-first environment</p><p className="mt-1 text-[11px] leading-4 text-muted-foreground">Evaluation workers execute sequentially on the local API process.</p><div className="mt-2 flex items-center gap-2 text-[10px] text-emerald-700"><span className="size-1.5 rounded-full bg-emerald-500" /> Development mode</div></div>
        </div>
      </aside>

      <main className="xl:pl-64">
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b bg-white/90 px-5 backdrop-blur sm:px-8">
          <div className="text-sm text-muted-foreground">Workspace <span className="px-2 text-slate-300">/</span><span className="font-medium text-slate-900">Overview</span></div>
          <Badge className="border-emerald-200 bg-emerald-50 text-emerald-700">Local development</Badge>
        </header>

        <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8" id="overview">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
            <div>
              <div className="flex items-center gap-2 text-xs font-medium text-primary"><FlaskConical className="size-3.5" /> Research workspace</div>
              <h1 className="mt-2 text-2xl font-semibold tracking-tight">LLM evaluation overview</h1>
              <p className="mt-1 max-w-2xl text-sm text-muted-foreground">Create a dataset, configure a model, and run a reproducible evaluation.</p>
            </div>
            <Button variant="outline" size="sm" onClick={() => void refreshData()} disabled={busy}><Activity className="size-4" /> Refresh workspace</Button>
          </div>

          {error && <div role="alert" className="mt-5 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800"><CircleAlert className="mt-0.5 size-4 shrink-0" />{error}</div>}
          {message && <div role="status" className="mt-5 flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800"><CheckCircle2 className="mt-0.5 size-4 shrink-0" />{message}</div>}

          <section className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Workspace metrics">
            <MetricCard label="Datasets" value={String(datasets.length)} note="Stored in Neon" icon={Database} />
            <MetricCard label="Configured models" value={String(models.length)} note="Provider configurations" icon={Boxes} />
            <MetricCard label="Experiments" value={String(experiments.length)} note="Saved experiment definitions" icon={FlaskConical} />
            <MetricCard label="Test cases" value={String(datasets.reduce((sum, item) => sum + item.test_case_count, 0))} note="Across latest dataset versions" icon={Layers3} />
          </section>

          <section id="datasets" className="mt-7 grid gap-4 xl:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Create a dataset</CardTitle><CardDescription>Creates dataset version 1 with one test case. Add richer import tooling in a later slice.</CardDescription></CardHeader>
              <CardContent>
                <form onSubmit={createDataset} className="space-y-3">
                  <label className="block text-xs font-medium">Dataset name<input required value={datasetName} onChange={(e) => setDatasetName(e.target.value)} className="mt-1.5 h-9 w-full rounded-lg border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-blue-200" /></label>
                  <label className="block text-xs font-medium">Test question<textarea required value={question} onChange={(e) => setQuestion(e.target.value)} rows={2} className="mt-1.5 w-full rounded-lg border bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-200" /></label>
                  <label className="block text-xs font-medium">Expected answer (optional)<input value={expectedAnswer} onChange={(e) => setExpectedAnswer(e.target.value)} className="mt-1.5 h-9 w-full rounded-lg border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-blue-200" /></label>
                  <Button type="submit" disabled={busy || !datasetName.trim() || !question.trim()}><Database className="size-4" /> Create dataset</Button>
                </form>
              </CardContent>
            </Card>

            <Card id="models">
              <CardHeader><CardTitle>Configure a model</CardTitle><CardDescription>Only the environment-variable name is stored. The API key stays in backend/.env.</CardDescription></CardHeader>
              <CardContent>
                <form onSubmit={createModel} className="space-y-3">
                  <label className="block text-xs font-medium">Configuration name<input required value={modelName} onChange={(e) => setModelName(e.target.value)} className="mt-1.5 h-9 w-full rounded-lg border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-blue-200" /></label>
                  <label className="block text-xs font-medium">Model identifier<input required value={modelId} onChange={(e) => setModelId(e.target.value)} className="mt-1.5 h-9 w-full rounded-lg border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-blue-200" /></label>
                  <label className="block text-xs font-medium">API base URL<input required type="url" value={endpointUrl} onChange={(e) => setEndpointUrl(e.target.value)} className="mt-1.5 h-9 w-full rounded-lg border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-blue-200" /></label>
                  <label className="block text-xs font-medium">Credential environment variable<input required value={apiKeyEnv} onChange={(e) => setApiKeyEnv(e.target.value.toUpperCase())} className="mt-1.5 h-9 w-full rounded-lg border bg-white px-3 font-mono text-sm outline-none focus:ring-2 focus:ring-blue-200" /></label>
                  <Button type="submit" variant="outline" disabled={busy || !modelName.trim() || !modelId.trim()}><Boxes className="size-4" /> Save model configuration</Button>
                </form>
              </CardContent>
            </Card>
          </section>

          <section id="experiments" className="mt-7 grid gap-4 xl:grid-cols-[1fr_0.85fr]">
            <Card>
              <CardHeader><CardTitle>Create an experiment</CardTitle><CardDescription>Bind a specific dataset version and model configuration to a research question.</CardDescription></CardHeader>
              <CardContent>
                <form onSubmit={createExperiment} className="space-y-3">
                  <label className="block text-xs font-medium">Experiment name<input required value={experimentName} onChange={(e) => setExperimentName(e.target.value)} className="mt-1.5 h-9 w-full rounded-lg border bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-blue-200" /></label>
                  <label className="block text-xs font-medium">Dataset version<select required value={selectedDatasetVersion} onChange={(e) => setSelectedDatasetVersion(e.target.value)} className="mt-1.5 h-9 w-full rounded-lg border bg-white px-3 text-sm" ><option value="">Select a dataset</option>{datasets.filter((item) => item.latest_version_id).map((item) => <option key={item.id} value={item.latest_version_id!}>{item.name} · v{item.latest_version} · {item.test_case_count} cases</option>)}</select></label>
                  <label className="block text-xs font-medium">Model configuration<select required value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)} className="mt-1.5 h-9 w-full rounded-lg border bg-white px-3 text-sm"><option value="">Select a model</option>{models.filter((item) => item.is_enabled).map((item) => <option key={item.id} value={item.id}>{item.name} · {item.model_id}</option>)}</select></label>
                  <label className="block text-xs font-medium">System prompt<textarea value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} rows={2} className="mt-1.5 w-full rounded-lg border bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-200" /></label>
                  <Button type="submit" disabled={busy || !selectedDatasetVersion || !selectedModel}><FlaskConical className="size-4" /> Create experiment</Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Saved experiments</CardTitle><CardDescription>Select an experiment to execute it locally.</CardDescription></CardHeader>
              <CardContent className="space-y-3">
                {loading ? <p className="text-sm text-muted-foreground">Loading workspace…</p> : experiments.length === 0 ? <div className="rounded-lg border border-dashed p-5 text-center text-sm text-muted-foreground">No experiments yet. Create the first one using the form.</div> : (
                  <>
                    <select value={selectedExperiment} onChange={(e) => { setSelectedExperiment(e.target.value); setLatestRun(null); }} className="h-9 w-full rounded-lg border bg-white px-3 text-sm">
                      {experiments.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                    </select>
                    {activeExperiment && <div className="rounded-lg border bg-slate-50 p-3"><p className="text-xs font-medium">{activeExperiment.name}</p><p className="mt-1 break-all font-mono text-[10px] text-muted-foreground">{activeExperiment.id}</p><Badge className="mt-2">{activeExperiment.status}</Badge></div>}
                    <Button onClick={() => void runExperiment()} disabled={busy || !activeExperiment} className="w-full">
                      {busy ? <LoaderCircle className="size-4 animate-spin" /> : <TerminalSquare className="size-4" />}
                      Run evaluation locally <ArrowRight className="ml-auto size-4" />
                    </Button>
                    <p className="text-[11px] leading-4 text-muted-foreground">Runs are sequential and limited to 100 test cases. Keep the API bound to localhost during this development stage.</p>
                  </>
                )}
              </CardContent>
            </Card>
          </section>

          <section id="latest-run" className="mt-7">
            <Card>
              <CardHeader className="flex-row items-start justify-between space-y-0">
                <div><CardTitle>Latest run results</CardTitle><CardDescription>Raw model output and deterministic score for each test case.</CardDescription></div>
                {latestRun && <Badge className="border-emerald-200 bg-emerald-50 text-emerald-700">{latestRun.status}</Badge>}
              </CardHeader>
              <CardContent>
                {!latestRun ? (
                  <div className="flex min-h-36 flex-col items-center justify-center rounded-lg border border-dashed bg-slate-50/70 px-6 text-center">
                    <BarChart3Fallback />
                    <p className="mt-3 text-sm font-medium">No run selected</p>
                    <p className="mt-1 text-xs text-muted-foreground">Create an experiment and run it to see persisted results here.</p>
                  </div>
                ) : (
                  <>
                    <div className="mb-4 grid gap-3 sm:grid-cols-4">
                      <div className="rounded-lg bg-slate-50 p-3"><p className="text-[11px] text-muted-foreground">Test cases</p><p className="mt-1 text-xl font-semibold">{latestRun.summary.total_cases ?? 0}</p></div>
                      <div className="rounded-lg bg-slate-50 p-3"><p className="text-[11px] text-muted-foreground">Scored</p><p className="mt-1 text-xl font-semibold">{latestRun.summary.scored ?? 0}</p></div>
                      <div className="rounded-lg bg-slate-50 p-3"><p className="text-[11px] text-muted-foreground">Mean exact-match</p><p className="mt-1 text-xl font-semibold">{meanScoreText}</p></div>
                      <div className="rounded-lg bg-slate-50 p-3"><p className="text-[11px] text-muted-foreground">Provider errors</p><p className="mt-1 text-xl font-semibold">{latestRun.summary.errors ?? 0}</p></div>
                    </div>
                    <div className="space-y-3">
                      {latestRun.results.map((result, index) => (
                        <div key={result.id} className="rounded-lg border p-4">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="text-xs font-semibold">Test case {index + 1}</p>
                            <div className="flex items-center gap-2">
                              <Badge>{result.failure_category || (result.score === 1 ? "matched" : "unscored")}</Badge>
                              {result.score !== null && <span className="font-mono text-xs">{(result.score * 100).toFixed(0)}%</span>}
                            </div>
                          </div>
                          <p className="mt-2 whitespace-pre-wrap text-sm">{result.model_output || result.error_message || "No output recorded."}</p>
                          <p className="mt-2 text-[10px] text-muted-foreground">{result.latency_ms ?? "—"} ms · {result.status}</p>
                        </div>
                      ))}
                    </div>
                    <p className="mt-4 break-all font-mono text-[10px] text-muted-foreground">Run ID: {latestRun.id}</p>
                  </>
                )}
              </CardContent>
            </Card>
          </section>
          <footer className="mt-8 flex flex-col justify-between gap-2 border-t pt-4 text-[11px] text-muted-foreground sm:flex-row"><span>LLM Reliability Evaluation Harness · Research build 0.2.0</span><span>Scores are only produced for supported deterministic metrics.</span></footer>
        </div>
      </main>
    </div>
  );
}

function BarChart3Fallback() {
  return <div className="flex size-11 items-center justify-center rounded-xl border bg-white text-slate-500"><Activity className="size-5" /></div>;
}
