import json
import os

def get_notebook_path(filename):
    home = os.path.expanduser("~")
    nb_dir = os.path.join(home, "retro-notebook-notebooks")
    os.makedirs(nb_dir, exist_ok=True)
    return os.path.join(nb_dir, filename)

def save_notebook(cells, filename):
    data = []
    for cell in cells:
        cell_type = cell.cell_type.currentText()
        entry = {
            "type": cell_type.lower(),
            "input": cell.input.toPlainText()
        }
        if cell_type == "Code":
            entry["output"] = cell.output.text()
        # Test cell outputs are intentionally NOT persisted
        data.append(entry)
    path = get_notebook_path(filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_notebook(filename):
    path = get_notebook_path(filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)  # gibt eine Liste von Zellen zurück