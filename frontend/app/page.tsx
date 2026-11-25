import {
  Activity, ArrowUpRight, BarChart3, BookOpenCheck, Boxes, Database,
  FlaskConical, Layers3, Search, ShieldCheck, TerminalSquare,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const metrics = [
  { label: "Experiments", value: "0", note: "No experiments created", icon: FlaskConical },
  { label: "Evaluation runs", value: "0", note: "No runs recorded", icon: Activity },
  { label: "Test cases", value: "0", note: "No dataset cases imported", icon: Layers3 },
  { label: "Failure rate", value: "—", note: "Available after first evaluation", icon: ShieldCheck },
];

const components = [
  { name: "API controller", detail: "FastAPI routes", state: "Scaffolded", icon: TerminalSquare },
  { name: "Experiment harness", detail: "Planning and scheduling", state: "Planned", icon: Activity },
  { name: "Local worker", detail: "One test case per task", state: "Planned", icon: Boxes },
  { name: "Evaluation engine", detail: "Metrics and failure labels", state: "Planned", icon: ShieldCheck },
  { name: "Neon database", detail: "PostgreSQL persistence", state: "Provisioned", icon: Database },
];

export default function HomePage() {
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
            <a className="flex items-center gap-3 rounded-lg bg-blue-50 px-3 py-2 font-medium text-blue-700" href="#"><BarChart3 className="size-4" /> Overview</a>
            <a className="flex items-center gap-3 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-50" href="#"><FlaskConical className="size-4" /> Experiments</a>
            <a className="flex items-center gap-3 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-50" href="#"><Layers3 className="size-4" /> Datasets</a>
            <a className="flex items-center gap-3 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-50" href="#"><Boxes className="size-4" /> Models</a>
            <a className="flex items-center gap-3 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-50" href="#"><ShieldCheck className="size-4" /> Failure explorer</a>
            <a className="flex items-center gap-3 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-50" href="#"><BookOpenCheck className="size-4" /> Research notes</a>
          </nav>
        </div>
        <div className="mt-auto border-t p-4">
          <div className="rounded-lg bg-slate-50 p-3"><p className="text-xs font-medium">Local-first environment</p><p className="mt-1 text-[11px] leading-4 text-muted-foreground">Evaluation workers run on your machine during development.</p><div className="mt-2 flex items-center gap-2 text-[10px] text-emerald-700"><span className="size-1.5 rounded-full bg-emerald-500" /> Development mode</div></div>
        </div>
      </aside>
      <main className="xl:pl-64">
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b bg-white/90 px-5 backdrop-blur sm:px-8">
          <div className="text-sm text-muted-foreground">Workspace <span className="px-2 text-slate-300">/</span><span className="font-medium text-slate-900">Overview</span></div>
          <div className="flex items-center gap-3"><Button variant="outline" size="sm"><Search className="size-3.5" /> Search</Button><Badge className="border-emerald-200 bg-emerald-50 text-emerald-700">Local development</Badge><div className="flex size-8 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">R</div></div>
        </header>
        <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
            <div><div className="flex items-center gap-2 text-xs font-medium text-primary"><FlaskConical className="size-3.5" /> Research workspace</div><h1 className="mt-2 text-2xl font-semibold tracking-tight">Overview</h1><p className="mt-1 max-w-2xl text-sm text-muted-foreground">Measure where language models fail. Build evidence for what makes them more reliable.</p></div>
            <Button disabled><FlaskConical className="size-4" /> New experiment <span className="ml-1 text-[10px] opacity-70">Coming next</span></Button>
          </div>
          <section className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Workspace metrics">
            {metrics.map((item) => { const Icon = item.icon; return <Card key={item.label}><CardContent className="flex items-start justify-between p-5"><div><p className="text-xs font-medium text-muted-foreground">{item.label}</p><p className="mt-2 text-2xl font-semibold tracking-tight tabular-nums">{item.value}</p><p className="mt-1 text-[11px] text-muted-foreground">{item.note}</p></div><div className="rounded-lg border bg-slate-50 p-2 text-slate-500"><Icon className="size-4" /></div></CardContent></Card>; })}
          </section>
          <section className="mt-6 grid gap-4 xl:grid-cols-[1.55fr_1fr]">
            <Card><CardHeader className="flex-row items-start justify-between space-y-0"><div><CardTitle>Experiment activity</CardTitle><CardDescription className="mt-1">Execution history will appear here.</CardDescription></div><Badge>Awaiting first run</Badge></CardHeader><CardContent><div className="flex min-h-[230px] flex-col items-center justify-center rounded-lg border border-dashed bg-slate-50/70 px-6 text-center"><div className="flex size-11 items-center justify-center rounded-xl border bg-white text-slate-500"><BarChart3 className="size-5" /></div><p className="mt-3 text-sm font-medium">No experiment data yet</p><p className="mt-1 max-w-sm text-xs leading-5 text-muted-foreground">When the evaluation pipeline is connected, this area will show run volume, completion status, and reliability trends.</p></div></CardContent></Card>
            <Card><CardHeader><CardTitle>System components</CardTitle><CardDescription>Boundaries for the first vertical slice.</CardDescription></CardHeader><CardContent className="space-y-3">{components.map((item) => { const Icon = item.icon; const ready = item.state === "Provisioned" || item.state === "Scaffolded"; return <div key={item.name} className="flex items-center gap-3"><div className="flex size-8 items-center justify-center rounded-lg border bg-white text-slate-500"><Icon className="size-4" /></div><div className="min-w-0 flex-1"><p className="text-xs font-medium">{item.name}</p><p className="text-[11px] text-muted-foreground">{item.detail}</p></div><span className={ready ? "text-[10px] font-medium text-emerald-700" : "text-[10px] text-muted-foreground"}>{item.state}</span></div>; })}</CardContent></Card>
          </section>
          <section className="mt-6 grid gap-4 lg:grid-cols-2">
            <Card><CardHeader><CardTitle>Start with a dataset</CardTitle><CardDescription>Versioned test cases are the foundation of reproducible evaluation.</CardDescription></CardHeader><CardContent><div className="flex items-center justify-between rounded-lg border bg-slate-50 p-4"><div className="flex items-center gap-3"><div className="rounded-lg border bg-white p-2"><Database className="size-4 text-slate-500" /></div><div><p className="text-xs font-medium">Dataset explorer</p><p className="text-[11px] text-muted-foreground">Import and inspect test cases</p></div></div><ArrowUpRight className="size-4 text-slate-400" /></div></CardContent></Card>
            <Card><CardHeader><CardTitle>Research principle</CardTitle><CardDescription>Keep measurements separate from interpretations.</CardDescription></CardHeader><CardContent><div className="rounded-lg border border-blue-100 bg-blue-50/70 p-4"><p className="text-sm font-medium text-blue-950">Evidence before conclusions</p><p className="mt-1 text-xs leading-5 text-blue-900/75">Store raw prompts, model outputs, configuration, metric values, and failure evidence. Every reported score should be traceable to its underlying test cases.</p></div></CardContent></Card>
          </section>
          <footer className="mt-8 flex flex-col justify-between gap-2 border-t pt-4 text-[11px] text-muted-foreground sm:flex-row"><span>LLM Reliability Evaluation Harness · Research build 0.1.0</span><span>Metrics will appear only after real runs are recorded.</span></footer>
        </div>
      </main>
    </div>
  );
}
