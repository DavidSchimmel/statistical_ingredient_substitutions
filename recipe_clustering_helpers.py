import numpy as np
import pandas as pd
import os
import pickle

from calc_recipe_ingredient_info_distances import collectSomeRecipeRecommendations, get_all_comments, get_all_mutual_info, evalRecommendations, getRecommendationsBasedOnMutualInformationRole, get_graph_nodes, get_all_gt_recipes, get_recipes_per_ingredient, get_recipes_per_ingredient_pairs, get_all_frequencies,getNaiveBayesRecommendations

def create_one_hot_ingredients_per_df(recipes, fg_nodes, file_path):
    not_ok_recipes_file = os.path.join(os.path.split(file_path)[0], "recipe_ids_with_ingrs_not_in_nodes.pkl")

    if os.path.isfile(file_path):
        with open(file_path, "rb") as file:
            one_hot_ingredients_per_recipe = pickle.load(file)
        with open(not_ok_recipes_file, "rb") as file:
            not_ok_recipes = pickle.load(file)
        return one_hot_ingredients_per_recipe, not_ok_recipes

    not_ok_recipes = []
    data = {node: [] for node in fg_nodes}
    data["recipe_id"] = []

    for recipe in recipes:
        recipe_ingredients = recipe["ingredients"]
        recipe_id = recipe["id"]

        recipe_nodes = []

        recipe_ok = True
        for recipe_ingredient in recipe_ingredients:
            recipe_ingredient_found = False
            for recipe_ingredient_variant in recipe_ingredient:
                if recipe_ingredient_variant in fg_nodes:
                    recipe_ingredient_found = True
                    recipe_nodes.append(recipe_ingredient_variant)
                    continue
            if not recipe_ingredient_found:
                recipe_ok = False

        if recipe_ok:
            for ingredient_name, row in data.items():
                if ingredient_name in recipe_nodes:
                    row.append(1)
                elif ingredient_name == "recipe_id":
                    row.append(recipe_id)
                else:
                    row.append(0)
        else:
            not_ok_recipes.append(recipe)

    one_hot_ingredients_per_recipe = pd.DataFrame(data=data, columns=list(data.keys()))
    one_hot_ingredients_per_recipe = one_hot_ingredients_per_recipe.set_index("recipe_id")

    with open(file_path, "wb") as file:
        pickle.dump(one_hot_ingredients_per_recipe, file)
    with open(not_ok_recipes_file, "wb") as file:
        pickle.dump(not_ok_recipes, file)

    return one_hot_ingredients_per_recipe, not_ok_recipes

def get_hamming_distances(recipe_id, one_hot_recipe_inrgedients):
    query_row = one_hot_recipe_inrgedients.loc[recipe_id]
    hamming_distances = []
    for i, row in one_hot_recipe_inrgedients.iterrows():
        if i != recipe_id:
            hamming_distance = sum(query_row != row)
            hamming_distances.append((i, hamming_distance))
    return hamming_distances

def get_jaccard_distances(recipe_id, one_hot_recipe_inrgedients):
    pass

def get_inverse_mi_roles():
    pass

def getRecipeIdsForSubTuples(recipes):
    recipe_ids_per_sub_tuple = {}
    for recipe in recipes:
        recipe_id = recipe["id"]
        sub_tuple = tuple(recipe["subs"])
        if len(sub_tuple) > 2:
            continue
        if sub_tuple in list(recipe_ids_per_sub_tuple.keys()):
            recipe_ids_per_sub_tuple[sub_tuple].append(recipe_id)
        else:
            recipe_ids_per_sub_tuple[sub_tuple] = []
            recipe_ids_per_sub_tuple[sub_tuple].append(recipe_id)
    return recipe_ids_per_sub_tuple

if __name__ == "__main__":
    ORDERED_RECIPE_IDS_PATH = os.path.abspath("./outputs/sorted_recipe_ids_list.pkl")
    TRAIN_COMMENTS_PATH = os.path.abspath("./inputs/train_comments_subs.pkl") # train recipes with substitutions
    TEST_COMMENTS_PATH = os.path.abspath("./inputs/test_comments_subs.pkl") # test recipes with substitutions
    VAL_COMMENTS_PATH = os.path.abspath("./inputs/val_comments_subs.pkl") # validation recipes with substitutions
    GRAPH_NODES_PATH = os.path.abspath("./inputs/graph/nodes_191120.csv")

    MUTUAL_INFO_DICT_PATH = os.path.abspath("./outputs/mutual_info_dict_with_self_info.pkl")
    RECIPES_PER_INGREDIENT_SMALL_PATH = os.path.abspath(
        "./outputs/recipes_per_ingredient_small.pkl"
    )
    RECIPES_PER_INGREDIENT_PAIRS_SMALL_PATH = os.path.abspath(
        "./outputs/recipes_per_ingredient_pairs_small.pkl"
    )
    PROCESSED_RECIPES_PATH = os.path.abspath("./outputs/processed_recipes.pkl")

    PATH_ONE_HOT_RECIPE_INGREDIENTS = os.path.abspath("./outputs/one_hot_recipe_ingredients.pkl")

    extended_recipes = get_all_comments(TRAIN_COMMENTS_PATH, TEST_COMMENTS_PATH, VAL_COMMENTS_PATH)
    ingredients = get_graph_nodes(GRAPH_NODES_PATH)

    one_hot_ingredients_per_recipe, not_ok_recipes = create_one_hot_ingredients_per_df(extended_recipes, ingredients,PATH_ONE_HOT_RECIPE_INGREDIENTS)

    filtered_columns = one_hot_ingredients_per_recipe.loc[:, (one_hot_ingredients_per_recipe.sum() > 0)]

    print(filtered_columns)