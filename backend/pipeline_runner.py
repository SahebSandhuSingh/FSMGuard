"""
FSMGuard Pipeline Runner
========================
Executes the complete 10-stage FSMGuard pipeline programmatically.
"""

import os
import sys
import json
import subprocess
from typing import Dict, Any, Optional, List
from pathlib import Path
import shutil
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PipelineRunner:
    """Manages execution of the FSMGuard pipeline stages"""
    
    def __init__(self, workspace_dir: str = "workspace"):
        """
        Initialize pipeline runner
        
        Args:
            workspace_dir: Directory for job workspaces
        """
        self.root_dir = Path(__file__).parent.parent
        self.workspace_dir = self.root_dir / workspace_dir
        self.workspace_dir.mkdir(exist_ok=True)
        
    def create_job_workspace(self, job_id: str) -> Path:
        """Create isolated workspace for a job"""
        job_dir = self.workspace_dir / job_id
        job_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (job_dir / "input").mkdir(exist_ok=True)
        (job_dir / "output").mkdir(exist_ok=True)
        (job_dir / "logs").mkdir(exist_ok=True)
        
        return job_dir
    
    def convert_systemverilog(self, input_file: Path, output_file: Path) -> bool:
        """
        Convert SystemVerilog to Verilog

        Returns:
            True if conversion successful
        """
        try:
            convert_script = self.root_dir / "convert_to_verilog.py"
            result = subprocess.run(
                ["python3", str(convert_script), str(input_file), str(output_file)],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Conversion error: {e}")
            return False

    def run_stages_1_to_4(self, job_dir: Path, verilog_file: Path) -> Dict[str, Any]:
        """
        Stages 1-4: Parsing, feature extraction, GNN detection.
        Delegates to run_fsmguard.py with --output-dir pointing at job_dir/output/.
        """
        output_dir = job_dir / "output"
        output_dir.mkdir(exist_ok=True)
        try:
            result = subprocess.run(
                [
                    "python3", str(self.root_dir / "run_fsmguard.py"),
                    str(verilog_file),
                    "--output-dir", str(output_dir),
                ],
                capture_output=True,
                text=True,
                timeout=180,
                cwd=str(self.root_dir),
            )
            stage4_file = output_dir / "stage4_detection.json"
            stage1_file = output_dir / "stage1_parsing.json"

            if not stage4_file.exists():
                # run_fsmguard.py may write stage4_report.json in some versions
                alt = output_dir / "stage4_report.json"
                if alt.exists():
                    stage4_file = alt

            if stage1_file.exists() and stage4_file.exists():
                with open(stage4_file) as f:
                    report = json.load(f)
                # Normalise: both "vulnerabilities" and "flagged_states" are used
                vulns = report.get("vulnerabilities") or report.get("flagged_states", [])
                return {
                    "success": True,
                    "vulnerabilities": vulns,
                    "output_file": str(stage4_file),
                    "stdout": result.stdout[-2000:],
                }
            else:
                return {
                    "success": False,
                    "error": "Stage 1-4 output files not found",
                    "stdout": result.stdout[-2000:],
                    "stderr": result.stderr[-2000:],
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

    def run_stages_5_to_10(self, job_dir: Path, input_file: Path) -> Dict[str, Any]:
        """
        Stages 5-10: Subgraph isolation, RL agent, patching, verification.
        Runs run_stages_5_10.py with cwd=job_dir so its hardcoded 'output/'
        paths resolve to job_dir/output/.
        Also symlinks templates/ and models/ into job_dir if needed.
        """
        # Ensure symlinks for resources the scripts need
        for resource in ("templates", "models", "fsm_gat_best.pth", "fsm_gat_model.pth",
                         "fsm_ppo_best.zip"):
            src = self.root_dir / resource
            dst = job_dir / resource
            if src.exists() and not dst.exists():
                try:
                    if src.is_dir():
                        os.symlink(src, dst)
                    else:
                        shutil.copy2(src, dst)
                except Exception:
                    pass

        # run_stages_5_10.py expects output/stage4_report.json;
        # run_fsmguard.py writes output/stage4_detection.json — bridge them
        detection_file = job_dir / "output" / "stage4_detection.json"
        report_file = job_dir / "output" / "stage4_report.json"
        if detection_file.exists() and not report_file.exists():
            shutil.copy2(detection_file, report_file)

        # Patch stage1_parsing.json to include input_file so run_stages_5_10.py
        # knows which Verilog file to load for patch generation
        stage1_file = job_dir / "output" / "stage1_parsing.json"
        if stage1_file.exists():
            try:
                with open(stage1_file) as f:
                    stage1_data = json.load(f)
                if "input_file" not in stage1_data:
                    # Use relative path from job_dir since that's the cwd for the subprocess
                    stage1_data["input_file"] = str(Path("input") / input_file.name)
                    with open(stage1_file, "w") as f:
                        json.dump(stage1_data, f, indent=2)
            except Exception:
                pass

        # Also copy the input file into job_dir/input/
        (job_dir / "input").mkdir(exist_ok=True)
        shutil.copy2(input_file, job_dir / "input" / input_file.name)

        try:
            result = subprocess.run(
                ["python3", str(self.root_dir / "run_stages_5_10.py")],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(job_dir),
                env={**os.environ, "PYTHONPATH": str(self.root_dir)},
            )

            output_dir = job_dir / "output"
            outputs: Dict[str, Any] = {}
            for fname in (
                "stage5_output.json",
                "stage8_comprehensive_report.json",
                "stage9_result.json",
                "fsm_report.json",
                "patched_fsm.v",
            ):
                fpath = output_dir / fname
                if fpath.exists():
                    if fname.endswith(".json"):
                        with open(fpath) as f:
                            outputs[fname] = json.load(f)
                    else:
                        outputs[fname] = str(fpath)

            return {
                "success": result.returncode == 0 or "patched_fsm.v" in outputs,
                "outputs": outputs,
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-2000:],
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

    def run_complete_pipeline(self, job_id: str, input_file: Path,
                              filename: str) -> Dict[str, Any]:
        """
        Run complete FSMGuard pipeline (stages 1-10).
        """
        results: Dict[str, Any] = {
            "job_id": job_id,
            "filename": filename,
            "stages": {},
        }

        try:
            job_dir = self.create_job_workspace(job_id)
            results["workspace"] = str(job_dir)

            # Convert .sv → .v if needed
            verilog_file = input_file
            if filename.endswith(".sv"):
                converted = job_dir / "input" / filename.replace(".sv", "_verilog.v")
                if self.convert_systemverilog(input_file, converted):
                    verilog_file = converted
                    results["converted"] = True
                else:
                    results["conversion_warning"] = "SV→V conversion failed, using original"

            # Stages 1-4
            print(f"[{job_id}] Stages 1-4: Parsing & Detection...")
            stage14 = self.run_stages_1_to_4(job_dir, verilog_file)
            results["stages"]["stage3_4"] = stage14   # keep key backend uses

            if not stage14["success"]:
                results["status"] = "failed"
                results["error"] = stage14.get("error", "Stages 1-4 failed")
                return results

            if not stage14.get("vulnerabilities"):
                results["status"] = "completed"
                results["message"] = "No vulnerabilities detected — design is safe"
                return results

            # Stages 5-10
            print(f"[{job_id}] Stages 5-10: Patching & Verification...")
            stage510 = self.run_stages_5_to_10(job_dir, verilog_file)
            results["stages"]["stage5_10"] = stage510

            if stage510["success"]:
                results["status"] = "completed"
                results["patched_file"] = stage510["outputs"].get("patched_fsm.v")
                results["final_report"] = stage510["outputs"].get("fsm_report.json")
            else:
                results["status"] = "partial"
                results["message"] = "Patching completed with warnings"

            return results

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            results["traceback"] = traceback.format_exc()
            return results
    
    def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve results for a completed job"""
        job_dir = self.workspace_dir / job_id
        if not job_dir.exists():
            return None
        
        results_file = job_dir / "results.json"
        if results_file.exists():
            with open(results_file, 'r') as f:
                return json.load(f)
        return None
    
    def save_job_results(self, job_id: str, results: Dict[str, Any]):
        """Save job results to disk"""
        job_dir = self.workspace_dir / job_id
        results_file = job_dir / "results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    def cleanup_job(self, job_id: str):
        """Remove job workspace"""
        job_dir = self.workspace_dir / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir)


if __name__ == "__main__":
    # Test the pipeline runner
    runner = PipelineRunner()
    
    # Example usage
    test_file = Path(__file__).parent.parent / "input" / "dma_timing_control_verilog.v"
    if test_file.exists():
        results = runner.run_complete_pipeline(
            "test-job-001",
            test_file,
            "dma_timing_control_verilog.v"
        )
        print(json.dumps(results, indent=2))
