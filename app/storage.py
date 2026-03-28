import json
import os

def get_notebook_path(filename):
    home = os.path.expanduser("~")
    nb_dir = os.path.join(home, "retro-notebook-notebooks")
    full_path = os.path.join(nb_dir, filename)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    return full_path

def cells_to_data(cells):
    """Serialize cell widgets to a list of plain dicts."""
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
    return data

def save_notebook(cells, filename):
    data = cells_to_data(cells)
    path = get_notebook_path(filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_notebook(filename):
    path = get_notebook_path(filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)  # gibt eine Liste von Zellen zurück