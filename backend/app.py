# backend/app.py
from flask import Flask, request, jsonify
import os
import traceback
from flask_cors import CORS




# Set your CSV path here (raw string to avoid Windows backslash escapes)
# CSV_PATH = r"C:\Users\kritS11\Desktop\Courses_Recommendation\data\udemy_courses.csv"
CSV_PATH = "../data/udemy_courses.csv"
# Put backend on top-level sys.path if needed (not usually required)
try:
    from recommender import create_recommender
except Exception:
    # If import fails because of path issues, give a helpful message
    raise

app = Flask(__name__)

CORS(app)


# Create recommender singleton and print some diagnostics
try:
    reco = create_recommender(CSV_PATH)
    # print detected columns so you can verify correctness in logs
    print("Recommender loaded successfully.")
    print("Detected CSV columns:", list(reco.df.columns))
    # if mapping exists, print it
    if hasattr(reco, "mapping"):
        print("Detected mapping:", reco.mapping)
except FileNotFoundError as e:
    print("CSV file not found. Please check CSV_PATH in app.py.")
    print("Tried path:", CSV_PATH)
    raise
except Exception as e:
    print("Error initializing recommender:")
    traceback.print_exc()
    raise



@app.route("/recommend")
def recommend():
    q = request.args.get("q") or request.args.get("name") or request.args.get("query")
    if not q:
        return jsonify({"error": "missing query parameter `q` (or `name`/`query`)"}), 400

    try:
        top_n = int(request.args.get("top_n", 4))
    except Exception:
        top_n = 4

    try:
        results = reco.recommend(q, top_n=top_n)
        return jsonify({"query": q, "results": results})
    except Exception as e:
        # Return error but also log full traceback in server logs
        traceback.print_exc()
        return jsonify({"error": "internal server error", "message": str(e)}), 500


if __name__ == "__main__":
    # When running directly, start Flask dev server
    # Note: do not use debug=True on production
    app.run(host="0.0.0.0", port=5000, debug=True)
