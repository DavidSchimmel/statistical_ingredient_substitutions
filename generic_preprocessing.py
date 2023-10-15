import os
import re
from fractions import Fraction
import json


def make_recipes_extended_dict(extended_recipes):
    """Creates a dictionary with recipe id as key and all info in extended_recipes recipes as value. Additionally, aggregates all GT substitutions in recipe["subs"] if we encounter more than one GT sub per recipe_id in the extended recipes traversal.

    Args:
        extended_recipes (_type_): _description_

    Returns:
        dict[recipe_id, recipe]: with collected GT subs.
    """
    recipes_extended_dict = {}
    for recipe in extended_recipes:
        recipe_id = recipe["id"]
        if recipe_id not in list(recipes_extended_dict.keys()):
            recipes_extended_dict[recipe_id] = recipe
            recipes_extended_dict[recipe_id]["subs_collection"] = []
        if isinstance(recipe["subs"][0], list):
            for sub_list in recipe["subs"]:
                recipes_extended_dict[recipe_id]["subs_collection"].append(sub_list)
        else:
            recipes_extended_dict[recipe_id]["subs_collection"].append(recipe["subs"])

    return recipes_extended_dict


    recipes_extended_dict = {}
    for recipe in extended_recipes:
        recipe_id = recipe["id"]
        sub_tuple = recipe["subs"]
        if recipe_id not in list(recipes_extended_dict.keys()):
            recipes_extended_dict[recipe_id] = recipe
            recipes_extended_dict[recipe_id]["subs"] = []
        if not isinstance(sub_tuple[0], list):
            recipes_extended_dict[recipe_id]["subs"].append([recipe["subs"]])
        else:
            recipes_extended_dict[recipe_id]["subs"].append(sub_tuple)
    return recipes_extended_dict

def getRecipesPerSubstitutionTuple(extended_recipes):
    """form the extendede recipes, adds the recipe id to a dict mappping substitution tuple to recipe ids in which the substitution tuple is (gismo) grount truth, if both tuple ingredients are contained in the recipes ingredient list.

    Args:
        extended_recipes (_type_): _description_

    Returns:
        dict: substitution_tuple: list(recipe_id)
    """
    recipes_per_substitution = {}
    recipes_in_which_sub_ingrs_are_not_in_ingr_list = []
    for extended_recipe in extended_recipes:
        recipe_id = extended_recipe["id"]
        gt_subs = extended_recipe["subs"]
        ingredients = extended_recipe["ingredients"]
        for gt_sub in gt_subs:
            source_is_in_ingredient_list = False
            target_is_in_ingredient_list = False
            for ingredient in ingredients:
                if gt_sub[0] in ingredient:
                    source_is_in_ingredient_list = True
                if gt_sub[1] in ingredient:
                    target_is_in_ingredient_list = True
            if source_is_in_ingredient_list and target_is_in_ingredient_list:
                if gt_sub in list(recipes_per_substitution.keys()):
                    recipes_per_substitution = []
                recipes_per_substitution[gt_sub].append(recipe_id)
            else:
                recipes_in_which_sub_ingrs_are_not_in_ingr_list.append(recipe_id)

    return recipes_per_substitution, recipes_in_which_sub_ingrs_are_not_in_ingr_list

##############

# Function to normalize quantities and units
def normalize_quantity(quantity_str):
    unmatched_quantity_name = None
    original_ingredient_name = quantity_str
    quantity_str = quantity_str.strip()
    # Handle common unit variations
    unit_mapping = {
        "pounds ": "pound",
        "cup ": "cup",
        "cups ": "cup",
        "tbsp ": "tablespoon",
        "tablespoons ": "tablespoon",
        "tablespoon ": "tablespoon",
        "tsp ": "teaspoon",
        "teaspoons ": "teaspoon",
        "clove ": "clove",
        "cloves ": "clove",
        "onion ": "onion",
        "onions ": "onion",
        "grams ": "gram",
        "oz ": "ounce",
        "ounces ": "ounce",
        "lb ": "pound",
        "lbs ": "pound",
        "g ": "gram",
    }
    for key, value in unit_mapping.items():
        quantity_str = quantity_str.replace(key, value)

    # Use regular expressions to extract quantities and fractions
    quantity_match = re.match(r"(\d+\s*(?:\d+/*\d+)?)\s*(\S.*)", quantity_str)
    if quantity_match:
        quantity = quantity_match.group(1).strip()
        ingredient = quantity_match.group(2)
        unit = None

        for unit_name in list(unit_mapping.values()):
            if unit_name in ingredient.lower():
                unit = unit_name
                ingredient = ingredient.replace(unit_name, "").strip()
                break

        if unit is None:
            unmatched_quantity_name = ingredient.strip().split(" ")[0].strip()
            print(unmatched_quantity_name)

        # # avg quantity range
        # if "-" in quantity:
        #     quantity_parts = [float(part.strip()) for part in quantity.split("-")]
        #     quantity = sum(quantity_parts) / len(quantity_parts)
        # Normalize fractions and convert to float
        fraction_parts = quantity.split()
        if unit != "gram":
            for i, fraction_part in enumerate(fraction_parts):
                if len(fraction_part) > 1 and fraction_part[-1] != "0":
                    fraction_parts[
                        i] = fraction_part[0] + "/" + fraction_part[1:]

        total_quantity = 0.0
        for part in fraction_parts:
            try:
                total_quantity += float(Fraction(part))
            except ValueError:
                pass  # Ignore non-fractional parts

        return total_quantity, unit, original_ingredient_name, unmatched_quantity_name

    return None, None, original_ingredient_name, None


# Function to convert quantities to grams
def convert_to_grams(quantity, unit):
    unit_to_grams = {
        "gram": 1,
        "ounce": 28.3495,
        "pound": 453.592,
        "cup": 236.588,
        "tablespoon": 14.7868,
        "teaspoon": 4.92892,
        "clove": 5,
        "onion": 100,
    }
    return quantity * unit_to_grams.get(unit, 1)


# Function to extract ingredients with quantities in grams
def extract_ingredients_with_normalized_quantities(ingredient_list):
    ingredients_w_quantities = {}
    unmatched_quantity_names = []
    # Split the text into lines

    for ingredient in ingredient_list:
        # Extract quantity and ingredient
        quantity, unit, ingredient, unmatched_quantity_name = normalize_quantity(
            ingredient)
        if unmatched_quantity_name is not None:
            if unmatched_quantity_name not in unmatched_quantity_names:
                unmatched_quantity_names.append(unmatched_quantity_name)
        if quantity is not None:
            quantity_in_grams = convert_to_grams(quantity, unit)
            ingredients_w_quantities[ingredient] = quantity_in_grams

    return ingredients_w_quantities, unmatched_quantity_names


if __name__ == "__main__":
    # load the recipes
    DRY_RUN = False

    GISMO_WITH_NAMES_AND_INSTRUCTIONS_PATH = os.path.abspath(
        "C:/UM/Master/FoodRecommendations/scrapbooks/food-recommender-scrapbooks/generated_data/extended_recipes_with_instructions_and_titles.json"
    )
    GISMO_WITH_QUANTITIES_PATH = os.path.abspath(
        "C:/UM/Master/FoodRecommendations/scrapbooks/food-recommender-scrapbooks/generated_data/extended_recipes_with_quantities.json"
    )

    with open(GISMO_WITH_NAMES_AND_INSTRUCTIONS_PATH,
              'r') as recipe_extended_with_original_info:
        extended_recipes = json.load(recipe_extended_with_original_info)
    # recipes_extended_dict = {
    #     recipe["id"]: recipe for recipe in extended_recipes
    # }

    unmatched_quantity_names = []

    for recipe in extended_recipes:
        ingredient_list = recipe["original_ingredients"]
        # Extract ingredients with quantities in grams
        ingredient_quantities, recipe_unmatched_quantity_names = extract_ingredients_with_normalized_quantities(
            ingredient_list)

        unmatched_quantity_names = set(unmatched_quantity_names).union(
            set(recipe_unmatched_quantity_names))

        recipe["ingredient_quantities"] = ingredient_quantities

    if not DRY_RUN:
        with open(GISMO_WITH_QUANTITIES_PATH,
                  "w") as gismo_recipes_with_quantities_file:
            json.dump(extended_recipes,
                      gismo_recipes_with_quantities_file,
                      indent=2)

        # sort
        # ingredient_w_quantities = dict(
        #     sorted(ingredient_w_quantities.items(),
        #            key=lambda item: item[1],
        #            reverse=True))

        # # Find the ingredient with the highest quantity
        # main_ingredient = list(ingredient_w_quantities.keys())[0]
        # main_ingredient_qty = list(ingredient_w_quantities.values())[0]

#example
# recipe_text = """'1 12 pound gramround beef'
# 1 -2 tsp range ingredient
# 1 pound dry ziti pasta
# 1 onion, chopped
# 1 pound lean ground beef
# 2 (26 ounce) jars spaghetti sauce
# 6 ounces provolone cheese, sliced
# 1 ½ cups sour cream
# 6 ounces mozzarella cheese, shredded
# 2 tablespoons grated Parmesan cheese
# """

# ingredient_list = recipe_text.split('\n')

# # Extract ingredients with quantities in grams
# ingredient_w_quantities = extract_ingredients_with_normalized_quantities(
#     ingredient_list)

# # sort
# ingredient_w_quantities = dict(
#     sorted(ingredient_w_quantities.items(),
#            key=lambda item: item[1],
#            reverse=True))

# # Find the ingredient with the highest quantity
# main_ingredient = list(ingredient_w_quantities.keys())[0]
# main_ingredient_qty = list(ingredient_w_quantities.values())[0]

# print("Main Ingredient:", main_ingredient)
# print("Quantity (in grams):", main_ingredient_qty)
