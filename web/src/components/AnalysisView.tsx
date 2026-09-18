import type { Analysis } from "../types/api";
import { Card, DetailList, Empty } from "./UI";

const sections: [string, string][] = [["Evidence quality", "evidence_quality"], ["Evidence gaps", "evidence_gap_details"], ["Conflicts", "evidence_conflicts"], ["Observed patterns", "observed_patterns"], ["Insights", "insights"], ["Innovation opportunities", "innovation_opportunities"], ["Innovation hypotheses", "innovation_hypotheses"]];
export function AnalysisView({ analysis }: { analysis?: Analysis }) {
  if (!analysis) return <Empty>Define a strategic question and run an exploratory analysis.</Empty>;
  const report = analysis.report;
  return <div className="results"><Card title="Problem framing"><p>{String(report.problem ?? report.strategic_problem ?? "The submitted strategic question frames this exploratory analysis.")}</p></Card>{sections.map(([title, key]) => report[key] ? <Card key={key} title={title}><DetailList value={report[key]} /></Card> : null)}<Card title="Uncertainty and provenance"><p>{analysis.responsible_ai}</p><h3>Evidence IDs</h3><ul className="id-list">{analysis.evidence_ids.map((id) => <li key={id}>{id}</li>)}</ul>{report.uncertainty !== undefined ? <DetailList value={report.uncertainty} /> : null}</Card></div>;
}
