"""
Run sentiment analysis on example_reviews.csv and print results.
"""
import pandas as pd
from csv_utils import detect_text_column, run_sentiment_on_df

def main():
    df = pd.read_csv("example_reviews.csv")
    text_col = detect_text_column(df)
    if not text_col:
        text_col = df.columns[0]
    print("Text column:", text_col)
    print("\nRunning sentiment analysis...\n")
    result = run_sentiment_on_df(df, text_col)
    counts = result["sentiment"].value_counts()
    print("=== SUMMARY ===")
    for label, count in counts.items():
        print(f"  {label.capitalize()}: {count}")
    print("\n=== EXAMPLE POSITIVE REVIEWS ===")
    for _, row in result[result["sentiment"] == "positive"].head(3).iterrows():
        print(f"  [{row['sentiment_confidence']:.2f}] {row[text_col][:80]}...")
    print("\n=== EXAMPLE NEGATIVE REVIEWS ===")
    for _, row in result[result["sentiment"] == "negative"].head(3).iterrows():
        print(f"  [{row['sentiment_confidence']:.2f}] {row[text_col][:80]}...")
    out_path = "example_reviews_with_sentiment.csv"
    result.to_csv(out_path, index=False)
    print(f"\nProcessed CSV saved to: {out_path}")
    print("\n--- Full result table ---")
    print(result.to_string())

if __name__ == "__main__":
    main()
