"""CLI entry point – same pipeline the Kaggle notebook runs."""

from crawler import run_pipeline


def main():
    df = run_pipeline()
    if df.empty:
        print("No violations detected.")
    else:
        print(f"\n{len(df)} violation frame(s) saved. See output/results.csv")


if __name__ == "__main__":
    main()
