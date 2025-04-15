from flask import Flask, jsonify
from pipeline_trend_analyzer.trend_analysis import compare_trends_extended, get_today_trends
from pipeline_trend_analyzer.trend_analysis import get_trends_by_date
from datetime import datetime

app = Flask(__name__)


@app.route("/api/trends/compare-ext", methods=["GET"])
def api_compare_trends():
    data = compare_trends_extended()
    return jsonify(data), 200


@app.route("/api/trends/today", methods=["GET"])
def api_trends_today():
    data = get_today_trends()
    return jsonify(data), 200


@app.route("/api/trends/<date_str>", methods=["GET"])
def api_trends_by_date(date_str):
    try:
        # Validate ISO format
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    result = get_trends_by_date(date_str)
    if result is None:
        return jsonify({"message": f"No trends found for {date_str}."}), 404
    return jsonify(result), 200


@app.route("/api/trends/forecast", methods=["GET"])
def get_forecasted_trends():
    predictions = "Output"
    return jsonify(predictions), 200


if __name__ == '__main__':
    app.run(debug=True)
