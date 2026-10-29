"""Flask backend: exposes both trees as a small JSON API."""
from flask import Flask, jsonify, render_template, request

from models import PedigreeTree, RankingBST

app = Flask(__name__)

pedigree = PedigreeTree.sample()
ranking = RankingBST.sample()


def error(message, status=400):
    return jsonify({"error": message}), status


def pedigree_payload():
    return {
        "tree": pedigree.to_dict(),
        "analysis": {
            "size": pedigree.size(),
            "height": pedigree.height(),
            "preorder": pedigree.preorder(),
            "inorder": pedigree.inorder(),
            "postorder": pedigree.postorder(),
            "level_order": pedigree.level_order(),
            "generations": pedigree.generations(),
            "repeated": pedigree.repeated_ancestors(),
        },
    }


def ranking_payload():
    low, high = ranking.minimum(), ranking.maximum()
    return {
        "tree": ranking.to_dict(),
        "ranking": ranking.ranking(),
        "size": ranking.size(),
        "height": ranking.height(),
        "lowest": low.name if low else None,
        "highest": high.name if high else None,
    }


@app.get("/")
def index():
    return render_template("index.html")


# ---------- pedigree ----------
@app.get("/api/pedigree")
def get_pedigree():
    return jsonify(pedigree_payload())


@app.post("/api/pedigree")
def add_ancestor():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    if not name:
        return error("El nombre del caballo es obligatorio.")
    year = data.get("birth_year")
    try:
        year = int(year) if year not in (None, "") else None
        if pedigree.root is None:
            pedigree.set_root(name, data.get("breed", ""), year)
        else:
            pedigree.add_ancestor(
                int(data.get("parent_id")), data.get("role"), name, data.get("breed", ""), year
            )
    except (ValueError, LookupError, TypeError) as exc:
        return error(str(exc))
    return jsonify(pedigree_payload())


@app.delete("/api/pedigree/<int:node_id>")
def remove_ancestor(node_id):
    try:
        pedigree.remove_subtree(node_id)
    except (ValueError, LookupError) as exc:
        return error(str(exc))
    return jsonify(pedigree_payload())


@app.get("/api/pedigree/<int:node_id>/path")
def pedigree_path(node_id):
    return jsonify({"path": pedigree.path_to(node_id)})


@app.post("/api/pedigree/reset")
def reset_pedigree():
    global pedigree
    pedigree = PedigreeTree.sample()
    return jsonify(pedigree_payload())


# ---------- ranking ----------
@app.get("/api/ranking")
def get_ranking():
    return jsonify(ranking_payload())


@app.post("/api/ranking")
def add_horse():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    if not name:
        return error("El nombre del caballo es obligatorio.")
    try:
        ranking.insert(name, float(data.get("points")), data.get("discipline", ""))
    except (ValueError, TypeError) as exc:
        return error("Los puntos deben ser un número." if "float" in str(exc) else str(exc))
    return jsonify(ranking_payload())


@app.delete("/api/ranking/<name>")
def delete_horse(name):
    try:
        ranking.delete(name)
    except LookupError as exc:
        return error(str(exc), 404)
    return jsonify(ranking_payload())


@app.get("/api/ranking/search")
def search_horse():
    node = ranking.find_by_name(request.args.get("name", ""))
    if node is None:
        return error("No se encontró el caballo.", 404)
    return jsonify({"name": node.name, "points": node.points, "discipline": node.discipline})


if __name__ == "__main__":
    app.run(debug=True)
