import json
import os

class IngredientSubstitutionQuestionBlock:
    Q_FIT_TEXT = "Does the suggested substitution fit the recipe?"
    Q_MAJOR_CHANGE_TEXT = "Would exchanging the ingredients require major changes to the recipe?"
    Q_SUBS_SELECTION = "Which of the following substitutions would you chose for the main ingredient of the recipe?"

    TEXT_CONTENT = """[[Block:@@sample_id@@]]

Title - @@recipe_title@@


Ingredient List - @@ingredient_list@@


Instruction List - @@instruction_list@@


Suggested Substitution - @@gt_sub@@


MC @@sample_id@@-fit. @@Q_FIT_TEXT@@

yes
no


MC @@sample_id@@-change. @@Q_MAJOR_CHANGE_TEXT@@

yes
no


MC @@sample_id@@-selection. @@Q_SUBS_SELECTION@@

@@substitute_suggestion_1@@
@@substitute_suggestion_2@@
@@substitute_suggestion_3@@
"""

    def __init__(self, gt_sub: list,
                 recipe_title: str,
                 recipe_ingredient_list: list,
                 recipe_instruction_list: list,
                 sub_options_list: list[str],
                 sample_id: int) -> None:
        self.gt_sub = [ingr.replace("_", " ") for ingr in gt_sub]
        self.recipe_title = recipe_title
        self.recipe_ingredient_list = [ingr.replace("_", " ") for ingr in recipe_ingredient_list]
        self.recipe_instruction_list = recipe_instruction_list
        self.sub_options_list = sub_options_list
        self.sample_id = sample_id

    def __str__(self) -> str:
        text_content = self.TEXT_CONTENT
        text_content = text_content.replace("@@sample_id@@", str(self.sample_id)) \
                                   .replace("@@recipe_title@@", self.recipe_title) \
                                   .replace("@@ingredient_list@@", ",\n".join(self.recipe_ingredient_list)) \
                                   .replace("@@instruction_list@@", ",\n".join(self.recipe_instruction_list)) \
                                   .replace("@@gt_sub@@", " -> ".join(self.gt_sub)) \
                                   .replace("@@Q_FIT_TEXT@@", self.Q_MAJOR_CHANGE_TEXT) \
                                   .replace("@@Q_MAJOR_CHANGE_TEXT@@", self.Q_MAJOR_CHANGE_TEXT) \
                                   .replace("@@Q_SUBS_SELECTION@@", self.Q_MAJOR_CHANGE_TEXT) \
                                   .replace("@@substitute_suggestion_1@@", self.sub_options_list[0]) \
                                   .replace("@@substitute_suggestion_2@@", self.sub_options_list[1]) \
                                   .replace("@@substitute_suggestion_3@@", self.sub_options_list[2])

        return text_content

def createQualtrixSurveyText(survey_data):

    survey_string = ""

    for gt_sub, recipe, sample_id in survey_data:
        question_block = IngredientSubstitutionQuestionBlock(gt_sub,
                                                             recipe["title"],
                                                             recipe["original_ingredients"],
                                                             recipe["instructions"],
                                                             ["A", "B", "C"],
                                                             sample_id)

        survey_string += str(question_block) + "\n\n"

        if sample_id > 2:
            return survey_string

    return survey_string


if __name__ == "__main__":
    DRY_RUN = False

    QUALTRICS_SURVEY_DATA_FILE_PATH = os.path.abspath("C:\\UM\\Repos\\statistical_ingredient_substitutions\\inputs\\suvey_question_set_500.json")
    QUALTRICS_SURVEY_TEXT_FILE_PATH = os.path.abspath("C:\\UM\\Repos\\statistical_ingredient_substitutions\\outputs\\suvey_500.txt")

    with open(QUALTRICS_SURVEY_DATA_FILE_PATH, "r") as qualstrics_data_file:
        survey_data = json.load(qualstrics_data_file)

    survey_text_content = createQualtrixSurveyText(survey_data)#.replace("\\n", "\n").replace("\n", "\n")

    if not DRY_RUN:
        with open(QUALTRICS_SURVEY_TEXT_FILE_PATH, "w") as qualtrics_survey_file:
            qualtrics_survey_file.write(survey_text_content)

    pass
