import csv
import json
import pickle
import os
import re
from enum import Enum
from collections import Counter

class questionTypeSuffixes(Enum):
    FIT = "fit"
    RECIPE_TASTE = "tastechange"
    RECIPE_NUTRITION = "nutruientschange"
    RECIPE_PROCESS = "processchange"
    RECIPE_CATEGORY = "categorychange"
    MAIN = "mainingr"
    SUBSELECTION = "selection"
    USERSUGGESTION = "usersuggestion"

INDIVIDUAL_RESPONSES = "individual_responses"
CONSENSUAL_ANSWERS = "consensual_answers"

def main():
    SURVEY_RESULTS_PATH = os.path.abspath("./survey_results")
    FUSED_RESULTS_PATH = os.path.abspath("./survey_results_processed/fused_results.pkl")
    SURVEY_QUESTION_SET_PATH = os.path.abspath("./outputs/survey final file/survey_recipes_enriched.json")
    SURVEY_SAMPLES_WITH_ANSWERS_PATH = os.path.abspath("./survey_results_processed/survey_samples_with_answers.pkl")

    if not os.path.exists(FUSED_RESULTS_PATH):
        fused_raw_results = fuseResultsChunks(SURVEY_RESULTS_PATH)

        results_dict = generateResponseDictionary(fused_raw_results)

        results_dict = addConsensualAnswers(results_dict)
        with open(FUSED_RESULTS_PATH, "wb") as fused_results_file:
            pickle.dump(results_dict, fused_results_file)
    else:
        with open(FUSED_RESULTS_PATH, "rb") as fused_results_file:
            results_dict = pickle.load(fused_results_file)

    if not os.path.exists(SURVEY_SAMPLES_WITH_ANSWERS_PATH):
        with open(SURVEY_QUESTION_SET_PATH, 'r') as file:
            survey_samples = json.load(file)

        survey_samples_with_answer = addAnswersToSurveySamples(results_dict, survey_samples)

        with open(SURVEY_SAMPLES_WITH_ANSWERS_PATH, "wb") as survey_samples_with_answers_file:
            pickle.dump(survey_samples_with_answer, survey_samples_with_answers_file)

    print("preprocessing done")

def fuseResultsChunks(results_path):
    survey_response_chunks = []
    survey_results_directory_fs = os.fsencode(results_path)
    for file in os.listdir(survey_results_directory_fs):
        filename = os.fsdecode(file)
        if filename.startswith("survey_500_") and filename.endswith(".csv"):
            file_path = os.path.join(results_path, filename)
            response_chunk = []
            with open(file_path) as chunk_csv:
                chunk_reader = csv.reader(chunk_csv)
                for row in chunk_reader:
                    if row:
                        response_chunk.append(row)
            if response_chunk:
                survey_response_chunks.append(response_chunk)

    return survey_response_chunks

def generateResponseDictionary(all_chunks: list[list]) -> dict:
    results_dict = {}
    for chunk in all_chunks:
        for i in range(len(chunk[0])):
            sample_id_list = re.findall(r"\d+", chunk[0][i])
            if not sample_id_list:
                continue
            sample_id = int(sample_id_list[0])
            if sample_id not in results_dict:
                results_dict[sample_id] = {"individual_responses": {
                    questionTypeSuffixes.FIT.value: [],
                    questionTypeSuffixes.RECIPE_TASTE.value: [],
                    questionTypeSuffixes.RECIPE_NUTRITION.value: [],
                    questionTypeSuffixes.RECIPE_PROCESS.value: [],
                    questionTypeSuffixes.RECIPE_CATEGORY.value: [],
                    questionTypeSuffixes.MAIN.value: [],
                    questionTypeSuffixes.SUBSELECTION.value: [],
                    questionTypeSuffixes.USERSUGGESTION.value: []
                }}

            attr = None
            if chunk[0][i].endswith(questionTypeSuffixes.FIT.value):
                attr = questionTypeSuffixes.FIT.value
            if chunk[0][i].endswith(questionTypeSuffixes.RECIPE_TASTE.value):
                attr = questionTypeSuffixes.RECIPE_TASTE.value
            if chunk[0][i].endswith(questionTypeSuffixes.RECIPE_NUTRITION.value):
                attr = questionTypeSuffixes.RECIPE_NUTRITION.value
            if chunk[0][i].endswith(questionTypeSuffixes.RECIPE_PROCESS.value):
                attr = questionTypeSuffixes.RECIPE_PROCESS.value
            if chunk[0][i].endswith(questionTypeSuffixes.RECIPE_CATEGORY.value):
                attr = questionTypeSuffixes.RECIPE_CATEGORY.value
            if chunk[0][i].endswith(questionTypeSuffixes.MAIN.value):
                attr = questionTypeSuffixes.MAIN.value
            if chunk[0][i].endswith(questionTypeSuffixes.SUBSELECTION.value):
                attr = questionTypeSuffixes.SUBSELECTION.value
            if chunk[0][i].endswith(questionTypeSuffixes.USERSUGGESTION.value):
                attr = questionTypeSuffixes.USERSUGGESTION.value

            if attr is None:
                continue

            for response in chunk[3:]:
                val = response[i]
                if not val:
                    continue
                if val == "yes":
                    val = 1
                if val == "no":
                    val = 0
                results_dict[sample_id]["individual_responses"][attr].append(val)

    return results_dict

def addConsensualAnswers(results_dict):
    for sample_id, result in list(results_dict.items()):
        individual_responses = result["individual_responses"]

        does_fit = getConesnsus(individual_responses[questionTypeSuffixes.FIT.value])
        does_change_taste = getConesnsus(individual_responses[questionTypeSuffixes.RECIPE_TASTE.value])
        does_change_nutrition = getConesnsus(individual_responses[questionTypeSuffixes.RECIPE_NUTRITION.value])
        does_change_process = getConesnsus(individual_responses[questionTypeSuffixes.RECIPE_PROCESS.value])
        does_change_category = getConesnsus(individual_responses[questionTypeSuffixes.RECIPE_CATEGORY.value])
        is_main_ingredient = individual_responses[questionTypeSuffixes.MAIN.value]
        sub_selection = getConesnsus(individual_responses[questionTypeSuffixes.SUBSELECTION.value], True)
        user_suggestions = individual_responses[questionTypeSuffixes.USERSUGGESTION.value]

        result["consensual_answers"] = {
            questionTypeSuffixes.FIT.value: does_fit,
            questionTypeSuffixes.RECIPE_TASTE.value: does_change_taste,
            questionTypeSuffixes.RECIPE_NUTRITION.value: does_change_nutrition,
            questionTypeSuffixes.RECIPE_PROCESS.value: does_change_process,
            questionTypeSuffixes.RECIPE_CATEGORY.value: does_change_category,
            questionTypeSuffixes.MAIN.value: is_main_ingredient,
            questionTypeSuffixes.SUBSELECTION.value: sub_selection,
            questionTypeSuffixes.USERSUGGESTION.value: user_suggestions
        }

        results_dict[sample_id] = result

    return results_dict

def getConesnsus(answers, is_multiple_choice = False):
    """Returns the consensus value for the presented answers.

    Args:
        answers (_type_): response_dict
        is_multiple_choice (bool, optional): If true, will get consensus via absolute majority of votes for all answers.. Defaults to False.

    Returns:
        _type_: _description_
    """
    consensus = None
    if len(answers) < 2:
        return consensus

    if not is_multiple_choice:
        if sum(answers) < (len(answers) / 2):
            consensus = 0
        elif sum(answers) > (len(answers) / 2):
            consensus = 1
    else:
        item_counts = Counter(answers)
        most_common = item_counts.most_common(1)

        # check if all distinct items are equally frequently suggested
        tie = all(count == most_common[0][1] for count in item_counts.values()) and len(item_counts) > 1

        if most_common and not tie and most_common[0][1] > len(answers) / 2:
            consensus = most_common[0][0]

    return consensus

def addAnswersToSurveySamples(results_dict, survey_samples):
    recipes = []

    for i in range(len(survey_samples)):
        result = results_dict[i]
        sample = survey_samples[i][1]
        sample_sub = survey_samples[i][0]
        sample["individual_responses"] = result["individual_responses"]
        sample["consensual_answers"] = result["consensual_answers"]
        sample["sample_sub"] = sample_sub
        recipes.append(sample)

    return recipes

if __name__ == "__main__":
    main()