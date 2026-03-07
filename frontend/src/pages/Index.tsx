import { useState } from "react";
import { useNavigate } from "react-router-dom";
import ScannerHeader from "@/components/ScannerHeader";
import VerilogInput from "@/components/VerilogInput";
import ScanResults from "@/components/ScanResults";
import { MOCK_VULNERABILITIES, Vulnerability } from "@/lib/mockData";

const Index = () => {
  const [isScanning, setIsScanning] = useState(false);
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>([]);
  const [scanned, setScanned] = useState(false);
  const navigate = useNavigate();

  const handleScan = (code: string) => {
    setIsScanning(true);
    setVulnerabilities([]);
    setScanned(false);

    setTimeout(() => {
      setIsScanning(false);
      setVulnerabilities(MOCK_VULNERABILITIES);
      setScanned(true);
    }, 3000);
  };

  const handleFixAll = () => {
    navigate("/fix", { state: { vulnerabilities } });
  };

  return (
    <div className="min-h-screen bg-background grid-bg relative">
      <div className="scan-line fixed inset-0 pointer-events-none z-50 opacity-30" />
      <div className="max-w-4xl mx-auto px-6 pb-16 relative z-10">
        <ScannerHeader />
        <VerilogInput onScan={handleScan} isScanning={isScanning} />
        {scanned && vulnerabilities.length > 0 && (
          <ScanResults vulnerabilities={vulnerabilities} onFix={handleFixAll} />
        )}
      </div>
    </div>
  );
};

export default Index;
