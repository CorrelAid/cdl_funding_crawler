from pathlib import Path
import pickle
import dictdiffer

if __name__ == "__main__":
    with (Path(__file__).parent / "data.pkl").open("rb") as fp:
        results = pickle.load(fp)

    for page, trial_results in results.items():
        print(f"Page: {page}")
        for result in trial_results:
            if result is None:
                print(f"No result page {page}")

            else:
                if (
                    "https://www.foerderdatenbank.de/FDB/Content/DE/Foerderprogramm/Land/Schleswig-Holstein/wohnprojekte-gruendungsfonds.html"
                    in result["urls"]
                ):
                    print(f"Found in page: {page}")
        for diff in list(dictdiffer.diff(trial_results[0], trial_results[1])):
            print(diff)

        for diff in list(dictdiffer.diff(trial_results[0], trial_results[2])):
            print(diff)

        for diff in list(dictdiffer.diff(trial_results[0], trial_results[3])):
            print(diff)

        for diff in list(dictdiffer.diff(trial_results[0], trial_results[4])):
            print(diff)

    for result in results[16]:
        print(result["urls"])

    print(set(results[16][2]["urls"]) - set(results[16][0]["urls"]))
    print(set(results[16][0]["urls"]) - set(results[16][2]["urls"]))
