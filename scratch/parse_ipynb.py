import json

notebook_path = "/Users/sahebsandhu/AIBSS-1/backend/live_view/dog_bite_detection_training.ipynb"
with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for idx, cell in enumerate(nb.get("cells", [])):
    if cell.get("cell_type") == "code":
        outputs = cell.get("outputs", [])
        if outputs:
            print(f"\n--- Cell {idx} (Execution Count {cell.get('execution_count')}) ---")
            for out in outputs:
                if out.get("output_type") == "stream" and out.get("name") == "stdout":
                    print("".join(out.get("text", [])))
                elif out.get("output_type") == "execute_result":
                    print("Execute Result:", out.get("data", {}).get("text/plain", ""))
