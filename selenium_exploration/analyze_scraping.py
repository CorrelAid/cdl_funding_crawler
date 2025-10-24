from collections import Counter
import dictdiffer
from pathlib import Path
import pickle

if __name__ == "__main__":
    with (Path(__file__).parent / "data.pkl").open("rb") as fp:
        meta_results = pickle.load(fp)

    for driver, results in meta_results.items():
        for page, trial_results in results.items():
            print(f"Page: {page}")
            for result in trial_results:
                if result is None:
                    print(f"No result page {page}")

            for trial_result in trial_results[1:]:
                for diff in list(dictdiffer.diff(trial_results[0], trial_result)):
                    print(diff)

    print([len(set(result["urls"])) for result in results[16]])
    print([len(result["urls"]) for result in results[16]])
    print([len(set(result["titles"])) for result in results[16]])
    print([len(result["titles"]) for result in results[16]])
    print(set(results[16][1]["urls"]) - set(results[16][2]["urls"]))
    print(set(results[16][1]["titles"]) - set(results[16][2]["titles"]))

    for result in results[16]:
        print(Counter(result["urls"]))
        print(Counter(result["titles"]))
