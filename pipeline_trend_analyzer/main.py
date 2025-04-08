from trend_analysis import analyze_sample_trends
from prediction import predict_top_words


def run_pipeline_trend_analyzer(sample_id = ""):
    analyze_sample_trends(sample_id)
    predict_top_words()


if __name__ == "__main__":
    run_pipeline_trend_analyzer()
