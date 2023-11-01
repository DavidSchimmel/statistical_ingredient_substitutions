import json
import os

def createQualtrixSurveyText(survey_data):
    text_content = "abc"
    pass

if __name__ == "__main__":
    DRY_RUN = True

    QUALTRICS_SURVEY_DATA_FILE_PATH = os.path.abspath("C:\\UM\\Repos\\statistical_ingredient_substitutions\\inputs\\suvey_question_set_500.json")
    QUALTRICS_SURVEY_TEXT_FILE_PATH = os.path.abspath("C:\\UM\\Repos\\statistical_ingredient_substitutions\\outputs\\suvey_500.txt")
    print(QUALTRICS_SURVEY_DATA_FILE_PATH)
    print(QUALTRICS_SURVEY_TEXT_FILE_PATH)

    with open(QUALTRICS_SURVEY_DATA_FILE_PATH, "r") as qualstrics_data_file:
        survey_data = json.load(qualstrics_data_file)


    survey_text_content = createQualtrixSurveyText(survey_data)

    if not DRY_RUN:
        with open(QUALTRICS_SURVEY_TEXT_FILE_PATH, "w") as qualstrics_survey_file:
            json.dump(survey_text_content, qualstrics_survey_file, indent=2)

    pass
