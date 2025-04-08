from classifier import classify_articles
from exec_cleaner import clean_articles
from pipeline_trend_analyzer.trend_analysis import analyze_sample_trends


def run_pipeline_sample():
    sample_temp = classify_articles()
    clean_articles(sample_temp)
    analyze_sample_trends(sample_temp)
    return "ALL DONE !"


if __name__ == "__main__":
    run_pipeline_sample()
