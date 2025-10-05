from pathlib import Path
import pickle
import dictdiffer

if __name__ == "__main__":
    with (Path(__file__).parent / "data.pkl").open("rb") as fp:
        results = pickle.load(fp)

    for page, trial_results in results.items():
        print(f"Page: {page}")
        for result in trial_results:
            if result is not None:
                del result["count"]
            else:
                print(f"No result page {page}")

        for diff in list(dictdiffer.diff(trial_results[0], trial_results[1])):
            print(diff)

        for diff in list(dictdiffer.diff(trial_results[0], trial_results[2])):
            print(diff)

        for diff in list(dictdiffer.diff(trial_results[0], trial_results[3])):
            print(diff)

        for diff in list(dictdiffer.diff(trial_results[0], trial_results[4])):
            print(diff)
