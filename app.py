import sys
import os
from flask import Flask, render_template, request, jsonify
from algorithms.automata import parse_automaton, validate_automaton
from algorithms.pda import parse_pda
from algorithms.resolution import solve_resolution
from algorithms.transformer import get_all_transforms
from flask import Response, stream_with_context
from algorithms.ai_explainer import explain_stream


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

#  ─────────────────────────────────────────────────────────Page Routes ─────────────────────────────────────────────────────────
@app.route("/index")
def welcome():
    return render_template("index.html")

@app.route("/")
def index():
    return render_template("welcome.html")

@app.route("/automata")
def automata():
    return render_template("automata.html")

@app.route("/resolution")
def resolution():
    return render_template("resolution.html")

@app.route("/transformer")
def transformer():
    return render_template("transformer.html")

@app.route("/about")
def about():
    return render_template("about.html")

#  ─────────────────────────────────────────────────────────API Routes ─────────────────────────────────────────────────────────

@app.route("/api/automata/simulate", methods=["POST"])
def api_automata_simulate():
    #Simulate finite automaton on input string
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate
    errors = validate_automaton(data)
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    try:
        fa = parse_automaton(data)
        input_string = data.get("input_string", "")

        result = fa.simulate(input_string)
        graph = fa.get_graph_data()

        return jsonify(
            {"success": True, "result": result, "graph": graph, "fa_type": fa.fa_type}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/automata/graph", methods=["POST"])
def api_automata_graph():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    errors = validate_automaton(data)
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    try:
        fa = parse_automaton(data)
        graph = fa.get_graph_data()
        return jsonify({"success": True, "graph": graph})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pda/simulate", methods=["POST"])
def api_pda_simulate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    pda, errors = parse_pda(data)
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    try:
        input_string = data.get("input_string", "")
        result = pda.simulate(input_string)
        graph = pda.get_graph_data()
        return jsonify({"success": True, "result": result, "graph": graph})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pda/graph", methods=["POST"])
def api_pda_graph():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    pda, errors = parse_pda(data)
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    try:
        graph = pda.get_graph_data()
        return jsonify({"success": True, "graph": graph})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/resolution/solve", methods=["POST"])
def api_resolution_solve():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    formula = data.get("formula", "").strip()
    if not formula:
        return jsonify({"error": "Formula cannot be empty"}), 400

    result = solve_resolution(formula)

    if not result["success"]:
        return jsonify({"error": result["error"]}), 400

    return jsonify(result)


@app.route("/api/transformer/transform", methods=["POST"])
def api_transformer_transform():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    formula = data.get("formula", "").strip()
    if not formula:
        return jsonify({"error": "Formula cannot be empty"}), 400

    result = get_all_transforms(formula)

    if not result["success"]:
        return jsonify({"error": result["error"]}), 400

    return jsonify(result)


#AI explainer route



@app.route("/api/explain/<module>", methods=["POST"])
def api_explain(module):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    def generate():
        try:
            for chunk in explain_stream(module, data):
                yield f"data: {json.dumps(chunk)}\n\n"
        except ValueError as e:
            yield f"data: {json.dumps('[Error] ' + str(e))}\n\n"
        except Exception as e:
            yield f"data: {json.dumps('[Error] AI explainer failed: ' + str(e))}\n\n"
        yield "data: [DONE]\n\n"

    import json as _json

    json = _json

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
