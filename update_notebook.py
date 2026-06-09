import json

def update_notebook():
    file_path = "data_pipeline/colab/pipeline.ipynb"
    with open(file_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
        
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            source = cell.get("source", [])
            new_source = []
            for i, line in enumerate(source):
                if line.strip() == "!pip install -q \\":
                    new_source.append("!apt-get update -qq && apt-get install -y -qq tesseract-ocr tesseract-ocr-mar\n")
                    new_source.append(line)
                elif line.strip() == "PyMuPDF":
                    new_source.append("    PyMuPDF \\\n")
                    new_source.append("    pytesseract \\\n")
                    new_source.append("    Pillow\n")
                else:
                    new_source.append(line)
            cell["source"] = new_source

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)

if __name__ == "__main__":
    update_notebook()
