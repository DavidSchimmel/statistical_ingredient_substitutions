import json
import os
import pickle

LAYER_1_PATH = os.path.abspath("./recipe1m/input/layer1.json") # load the layer1.json file form [here](https://www.kaggle.com/code/dnyaneshpainjane/recipe1m-preprocessing/input)
LAYER_1_INSTRUCTIONS_PATH = os.path.abspath("./recipe1m/output/layer1_all_instructions.json")
LAYER_1_RECIPE_NAME_PATH = os.path.abspath("./recipe1m/output/layer1_all_recipe_names.json")

GISMO_RECIPES_PATH = os.path.abspath("./recipe1m/output/extended_recipes.pkl")
GISMO_WITH_INSTRUCTIONS_PATH = os.path.abspath("./recipe1m/output/extended_recipes_with_instructions.json")

GISMO_WITH_NAMES_AND_INSTRUCTIONS_PATH = os.path.abspath("./recipe1m/output/extended_recipes_with_instructions_and_titles.json")

GISMO_TRAIN_COMMENTS_PATH = os.path.abspath("./inputs/train_comments_subs.pkl")
GISMO_TEST_COMMENTS_PATH = os.path.abspath("./inputs/test_comments_subs.pkl")
GISMO_VAL_COMMENTS_PATH = os.path.abspath("./inputs/val_comments_subs.pkl")


DO_WRITE_INSTRUCTION_FILE = True
DO_WRITE_RECIPE_NAME_FILE = True
DO_WRITE_GISMO_INSTRUCTION_FILE = True
DO_WRITE_GISMO_RECIPE_NAME_AND_INSTRUCTIONS_FILE = True

def get_all_comments(train_set_path, test_set_path, val_set_path, extended_recipes_path):
    if os.path.isfile(extended_recipes_path):
        with open(extended_recipes_path, "rb") as extended_recipes_file:
            all_comments = pickle.load(extended_recipes_file)
            return all_comments

    with open(train_set_path, "rb") as train_comments_file:
        train_comments = pickle.load(train_comments_file)
    with open(test_set_path, "rb") as test_comments_file:
        test_comments = pickle.load(test_comments_file)
    with open(val_set_path, "rb") as val_comments_file:
        val_comments = pickle.load(val_comments_file)

    all_comments = train_comments + test_comments + val_comments

    with open(extended_recipes_path, "wb") as extended_recipes_path:
        pickle.dump(all_comments, extended_recipes_path)

    return all_comments

if not os.path.isfile(GISMO_RECIPES_PATH):
    all_comments = get_all_comments(GISMO_TRAIN_COMMENTS_PATH, GISMO_TEST_COMMENTS_PATH, GISMO_VAL_COMMENTS_PATH, GISMO_RECIPES_PATH)

if DO_WRITE_INSTRUCTION_FILE:
    with open(LAYER_1_PATH, 'r') as layer_1_file:
        layer1 = json.load(layer_1_file)
    instruction_for_recipe_id = {
        recipe["id"]: recipe["instructions"] for recipe in layer1
    }

    for recipe_id, instruction_convoluted in instruction_for_recipe_id.items():
        instruction_array = [step["text"] for step in instruction_convoluted]
        instruction_for_recipe_id[recipe_id] = instruction_array

    with open(LAYER_1_INSTRUCTIONS_PATH, 'w') as json_file:
        json.dump(instruction_for_recipe_id, json_file, indent=2)

if DO_WRITE_RECIPE_NAME_FILE:
    with open(LAYER_1_PATH, 'r') as layer_1_file:
        layer1 = json.load(layer_1_file)
    names_for_recipe_id = {recipe["id"]: recipe["title"] for recipe in layer1}

    with open(LAYER_1_RECIPE_NAME_PATH, 'w') as json_file:
        json.dump(names_for_recipe_id, json_file, indent=2)

if DO_WRITE_GISMO_INSTRUCTION_FILE:
    with open(LAYER_1_INSTRUCTIONS_PATH, 'r') as layer_1_instruction_file, open(
            GISMO_RECIPES_PATH, 'rb') as gismo_recipe_file, open(
                GISMO_WITH_INSTRUCTIONS_PATH,
                "wb") as gismo_recipes_with_instruction_file:
        layer1_instructions = json.load(layer_1_instruction_file)

        gismo_recipes = pickle.load(gismo_recipe_file)

        for recipe in gismo_recipes:
            id = recipe["id"]
            instruction_array = layer1_instructions[id]
            recipe["instructions"] = instruction_array

        pickle.dump(gismo_recipes, gismo_recipes_with_instruction_file)


def get_original_ingredient_list():
    with open(LAYER_1_PATH, 'r') as layer_1_file:
        layer1 = json.load(layer_1_file)
    instructions_for_recipe_id = {
        recipe["id"]: recipe["ingredients"] for recipe in layer1
    }
    original_instructions_for_recipe_id = {}
    for recipe_id, ingredient_list in instructions_for_recipe_id.items():
        original_instructions_for_recipe_id[recipe_id] = [
            ingredient["text"] for ingredient in ingredient_list
        ]
    return original_instructions_for_recipe_id


if DO_WRITE_GISMO_RECIPE_NAME_AND_INSTRUCTIONS_FILE:
    with open(LAYER_1_INSTRUCTIONS_PATH, 'r') as layer_1_instruction_file, open(
            LAYER_1_RECIPE_NAME_PATH, 'r') as layer_1_name_file, open(
                GISMO_RECIPES_PATH, 'rb') as gismo_recipe_file, open(
                    GISMO_WITH_NAMES_AND_INSTRUCTIONS_PATH,
                    "wb") as gismo_recipes_with_instruction_and_names_file:
        layer1_instructions = json.load(layer_1_instruction_file)
        layer1_names = json.load(layer_1_name_file)
        layer1_original_ingredients = get_original_ingredient_list()

        gismo_recipes = pickle.load(gismo_recipe_file)

        for recipe in gismo_recipes:
            id = recipe["id"]
            instruction_array = layer1_instructions[id]
            recipe_name = layer1_names[id]
            recipe["instructions"] = instruction_array
            recipe["title"] = recipe_name
            recipe["original_ingredients"] = layer1_original_ingredients[id]

        with open(GISMO_WITH_NAMES_AND_INSTRUCTIONS_PATH,
                  "w") as gismo_recipes_with_instruction_and_names_file:
            json.dump(gismo_recipes,
                      gismo_recipes_with_instruction_and_names_file,
                      indent=2)

        # pickle.dump(gismo_recipes,
        #             gismo_recipes_with_instruction_and_names_file)
