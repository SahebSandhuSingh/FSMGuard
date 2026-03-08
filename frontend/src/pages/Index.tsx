import { useState } from "react";
import { useNavigate } from "react-router-dom";
import ScannerHeader from "@/components/ScannerHeader";
import VerilogInput from "@/components/VerilogInput";
import ScanResults from "@/components/ScanResults";
import { Vulnerability } from "@/lib/mockData";
import { uploadVerilogText, startAnalysis, pollUntilDone, getResults } from "@/lib/api";

// Map backend flagged_states → frontend Vulnerability[]
function mapToVulnerabilities(flaggedStates: Array<{
  state_name: string;
  risk_score: number;
  severity: string;
  cwe: string;
  cwe_label: string;
  recommended_fix: string;
  attack_path: string;
}>): Vulnerability[] {
  const severityMap: Record<string, "critical" | "high" | "medium" | "low"> = {
    CRITICAL: "critical",
    HIGH: "high",
    MEDIUM: "medium",
    LOW: "low",
  };
  return flaggedStates.map((s, i) => ({
    id: `vuln-${String(i + 1).padStart(3, "0")}`,
    title: `${s.cwe}: ${s.cwe_label}`,
    severity: severityMap[s.severity?.toUpperCase()] ?? "medium",
    state: s.state_name,
    description: `State "${s.state_name}" is vulnerable (risk score: ${s.risk_score.toFixed(3)}). Attack path: ${s.attack_path}.`,
    line: 0,
    patchedCode: `// ${s.recommended_fix} applied to ${s.state_name}`,
    solution: `Apply ${s.recommended_fix} to state ${s.state_name}`,
  }));
}

const Index = () => {
  const [isScanning, setIsScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>([]);
  const [scanned, setScanned] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleScan = async (code: string) => {
    setIsScanning(true);
    setVulnerabilities([]);
    setScanned(false);
    setScanError(null);

    try {
      const { job_id } = await uploadVerilogText(code);
      setJobId(job_id);
      await startAnalysis(job_id);
      await pollUntilDone(job_id, () => {});
      const results = await getResults(job_id);

      // Prefer backend-shaped vulnerability_list; fall back to mapping stage3_4 data
      let vulns: Vulnerability[];
      if (results.vulnerability_list && results.vulnerability_list.length > 0) {
        vulns = results.vulnerability_list as unknown as Vulnerability[];
      } else {
        const flagged = (results.stages as Record<string, unknown> | undefined)
          ?.["stage3_4"] as Record<string, unknown> | undefined;
        const flaggedStates = (flagged?.["vulnerabilities"] as Array<{
          state_name: string; risk_score: number; severity: string;
          cwe: string; cwe_label: string; recommended_fix: string; attack_path: string;
        }>) ?? [];
        vulns = mapToVulnerabilities(flaggedStates);
      }

      setVulnerabilities(vulns);
      setScanned(true);
    } catch (err) {
      setScanError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setIsScanning(false);
    }
  };

  const handleFixAll = () => {
    navigate("/fix", { state: { vulnerabilities, jobId } });
  };

  return (
    <div className="min-h-screen bg-background grid-bg relative">
      <div className="scan-line fixed inset-0 pointer-events-none z-50 opacity-30" />
      <div className="max-w-4xl mx-auto px-6 pb-16 relative z-10">
        <ScannerHeader />
        <VerilogInput onScan={handleScan} isScanning={isScanning} />
        {scanError && (
          <div className="mt-4 p-4 border border-destructive/40 rounded-lg bg-destructive/10 font-mono text-sm text-destructive">
            Error: {scanError}
          </div>
        )}
        {scanned && vulnerabilities.length > 0 && (
          <ScanResults vulnerabilities={vulnerabilities} onFix={handleFixAll} />
        )}
        {scanned && vulnerabilities.length === 0 && !scanError && (
          <div className="mt-4 p-4 border border-primary/20 rounded-lg bg-card font-mono text-sm text-primary text-center">
            No vulnerabilities detected — design appears safe.
          </div>
        )}
      </div>
    </div>
  );
};

export default Index;