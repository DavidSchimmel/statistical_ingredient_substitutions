import json
import os


class IngredientSubstitutionQuestionBlock:
    Q_FIT_TEXT = "Does the suggested substitution fit the recipe?"
    Q_MAJOR_CHANGE_TEXT = (
        "Would exchanging the ingredients require major changes to the recipe?"
    )
    Q_SUBS_SELECTION = (
        "Which of the following substitutions would you chose for \"@@main_ingredient@@\"?"
    )

    TEXT_CONTENT = """[[Block:@@sample_id@@]]

Title - @@recipe_title@@


Ingredient List - @@ingredient_list@@


Instruction List - @@instruction_list@@


Suggested Substitution - @@gt_sub@@


MC@@sample_id@@fit. @@Q_FIT_TEXT@@

yes
no


MC@@sample_id@@change. @@Q_MAJOR_CHANGE_TEXT@@

yes
no


MC@@sample_id@@selection. @@Q_SUBS_SELECTION@@

@@substitute_suggestion_1@@
@@substitute_suggestion_2@@
@@substitute_suggestion_3@@
"""

    TEXT_CONTENT_ADVANCED = """[[AdvancedFormat]]

[[Block:@@sample_id@@]]

[[Question:Text]]
Title - @@recipe_title@@

[[Question:Text]]
Ingredient List - @@ingredient_list@@

[[Question:Text]]
Instruction List - @@instruction_list@@

[[Question:Text]]
Suggested Substitution - (@@gt_sub@@)

[[Question:MC:SingleAnswer:Horizontal]]
[[ID:MC@@sample_id@@fit]]
@@Q_FIT_TEXT@@

[[Choices]]
yes
no

[[Question:MC:SingleAnswer:Horizontal]]
[[ID:MC@@sample_id@@tastechange]]
Does this substitution imply a major change to the meal's taste?

[[Choices]]
yes
no
[[Question:MC:SingleAnswer:Horizontal]]
[[ID:MC@@sample_id@@nutruientschange]]
Does this substitution imply a major change to the meal's nutritional profile?

[[Choices]]
yes
no

[[Question:MC:SingleAnswer:Horizontal]]
[[ID:MC@@sample_id@@processchange]]
Does this substitution require major modifications to the cooking process (i.e. instruction set)?

[[Choices]]
yes
no

[[Question:MC:SingleAnswer:Horizontal]]
[[ID:MC@@sample_id@@categorychange]]
Does the substitution change the food category from the exchanged ingredient (i.e. swapping a meat for a vegetarian option or changing ingredients that do not cause the same cross-allergies)?

[[Choices]]
yes
no

[[Question:TE]]
[[ID:MC@@sample_id@@mainingr]]
Is "@@main_ingredient@@" the main ingredient of the recipe? If not, which one is the main ingredient?

[[Question:MC:SingleAnswer:Horizontal]]
[[ID:MC@@sample_id@@selection]]
@@Q_SUBS_SELECTION@@

[[Choices]]
@@substitute_suggestion_1@@
@@substitute_suggestion_2@@
@@substitute_suggestion_3@@
other

[[Question:TE]]
[[ID:MC@@sample_id@@usersuggestion]]
What substitution do you suggest instead (if you answered other)?

"""

    def __init__(
        self,
        gt_sub: list,
        assumed_main_ingredient: str,
        recipe_title: str,
        recipe_ingredient_list: list,
        recipe_instruction_list: list,
        sub_options_list: list[str],
        sample_id: int,
        do_use_advanced: bool,
    ) -> None:
        self.gt_sub = [ingr.replace("_", " ") for ingr in gt_sub]
        self.assumed_main_ingredient = assumed_main_ingredient
        self.recipe_title = recipe_title
        self.recipe_ingredient_list = [
            ingr.replace("_", " ") for ingr in recipe_ingredient_list
        ]
        self.recipe_instruction_list = recipe_instruction_list
        self.sub_options_list = sub_options_list
        self.sample_id = sample_id
        self.do_use_advanced = do_use_advanced

    def __str__(self) -> str:
        text_content = (
            self.TEXT_CONTENT_ADVANCED if self.do_use_advanced else self.TEXT_CONTENT
        )

        text_content = (
            text_content.replace("@@sample_id@@", str(self.sample_id))
            .replace("@@recipe_title@@", self.recipe_title)
            .replace("@@ingredient_list@@", ";\n".join(self.recipe_ingredient_list))
            .replace("@@instruction_list@@", ";\n".join(self.recipe_instruction_list))
            .replace("@@gt_sub@@", " -> ".join(self.gt_sub))
            .replace("@@Q_FIT_TEXT@@", self.Q_FIT_TEXT)
            .replace("@@Q_MAJOR_CHANGE_TEXT@@", self.Q_MAJOR_CHANGE_TEXT)
            .replace("@@Q_SUBS_SELECTION@@", self.Q_SUBS_SELECTION)
            .replace("@@substitute_suggestion_1@@", self.sub_options_list[0])
            .replace("@@substitute_suggestion_2@@", self.sub_options_list[1])
            .replace("@@substitute_suggestion_3@@", self.sub_options_list[2])
            .replace("@@main_ingredient@@", str(self.assumed_main_ingredient))
        )

        return text_content


def createQualtrixSurveyTexts(survey_data, chunk_limit = 50, do_use_advanced = True):
    survey_strings = [""]

    n_samples_per_chunk_counter = 0
    for gt_sub, recipe, sample_id in survey_data:
        question_block = IngredientSubstitutionQuestionBlock(
            gt_sub,
            recipe["main_ingredient"],
            recipe["title"],
            recipe["original_ingredients"],
            recipe["instructions"],
            recipe["substitute_suggestions"],
            sample_id,
            do_use_advanced,
        )

        survey_strings[-1] += str(question_block) + "\n\n"

        n_samples_per_chunk_counter += 1
        if n_samples_per_chunk_counter >= chunk_limit:
            survey_strings.append("")
            n_samples_per_chunk_counter = 0


    if not survey_strings[-1]:
        survey_strings.pop()
    return survey_strings


if __name__ == "__main__":
    DRY_RUN = False

    QUALTRICS_SURVEY_DATA_ORIG_FILE_PATH = os.path.abspath("./inputs/suvey_question_set_500.json")
    QUALTRICS_SURVEY_DATA_FILE_PATH = os.path.abspath("./inputs/survey_recipes_cgpt_suggestions.json")
    QUALTRICS_SURVEY_TEXT_DIR_PATH = os.path.abspath("./outputs/survey_import_files/")

    with open(QUALTRICS_SURVEY_DATA_FILE_PATH, "r") as qualstrics_data_file:
        survey_data = json.load(qualstrics_data_file)

    survey_text_contents = createQualtrixSurveyTexts(
        survey_data, 50, True
    )  # .replace("\\n", "\n").replace("\n", "\n")

    if not DRY_RUN:
        # if the dir does not exist yet, create it
        if not os.path.exists(QUALTRICS_SURVEY_TEXT_DIR_PATH):
            os.makedirs(QUALTRICS_SURVEY_TEXT_DIR_PATH)

        for chunk, survey_text_content in enumerate(survey_text_contents):
            file_name = f"survey_500-{chunk}.txt"
            file_path = os.path.join(QUALTRICS_SURVEY_TEXT_DIR_PATH, file_name)
            with open(file_path, "w") as qualtrics_survey_file:
                qualtrics_survey_file.write(survey_text_content)
