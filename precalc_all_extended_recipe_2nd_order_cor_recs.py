import csv
import json
import os
import pandas as pd
import pickle
import torch

from calc_recipe_ingredient_info_distances import get_all_comments, getDistancesForTransposedLists
from sklearn.metrics.pairwise import cosine_similarity

def make_recipes_extended_dict(extended_recipes):
    """Creates a dictionary with recipe id as key and all info in extended_recipes recipes as value. Additionally, aggregates all GT substitutions in recipe["subs"] if we encounter more than one GT sub per recipe_id in the extended recipes traversal. Copied from my statistical_ingredient_substitutions repo

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


def load_gismo_node_data(file_path):
    node_id2name = {}
    node_name2id = {}
    node_id2type = {}
    ingredients_cnt = []
    compounds_cnt = []
    node_id2count = {}
    node_count2id = {}
    counter = 1  # start with 1 to reserve 0 for padding
    with open(file_path, "r") as nodes_file:
        csv_reader = csv.DictReader(nodes_file)
        for row in csv_reader:
            node_id = int(row["node_id"])
            node_type = row["node_type"]
            node_id2name[node_id] = row["name"]
            node_name2id[row["name"]] = node_id
            node_id2type[node_id] = node_type
            if "ingredient" in node_type:
                ingredients_cnt.append(counter)
            else:
                compounds_cnt.append(counter)
            node_id2count[node_id] = counter
            node_count2id[counter] = node_id
            counter += 1
    nnodes = len(node_id2name)
    print("#nodes:", nnodes)
    print("#ingredient nodes:", len(ingredients_cnt))
    print("#compound nodes:", len(compounds_cnt))
    return (
        node_id2count,
        node_count2id,
        node_id2name,
        node_name2id,
        ingredients_cnt,
        node_id2name,
        nnodes,
    )

def load_gismo_ingredient_names(file_path):
    ingredient_names = []
    counter = 1  # start with 1 to reserve 0 for padding
    with open(file_path, "r") as nodes_file:
        csv_reader = csv.DictReader(nodes_file)
        for row in csv_reader:
            node_type = row["node_type"]
            if "ingredient" in node_type:
                ingredient_names.append(row["name"])
            counter += 1
    print("#nodes:", len(ingredient_names))
    return ingredient_names


def verify_recipe_data(recipes_extended_dict, all_comments) -> None:
    recipes_not_found = []
    comments_not_found = []

    for recipe_id in recipes_extended_dict:
        recipe_found = False
        for comments in all_comments:
            if recipe_id == comments["id"]:
                recipe_found = True
                break

        if not recipe_found:
            recipes_not_found.append(recipes_extended_dict["recipe_id"])

    for comment in all_comments:
        comment_found = True
        for recipe_id in recipes_extended_dict:
            if comment["id"] == recipe_id:
                comment_found = True
                break
        if not comment_found:
            comments_not_found.append(comment)

    return recipes_not_found, comments_not_found


def calc_all_coscine_substitutabilities_2_dict(all_comments, mutual_info_dict):
    skipped_recipe_ids = []
    # direct_source_mutual_info_recommendations = {}
    # cosine_similarity_role_recommendations = {}
    substitutabilities = {}

    test_counter = 0

    # get results over all requested recipes
    for comment in all_comments:
        test_counter += 1
        if test_counter % 1000 == 0:
            print(test_counter)

        recipe_id = comment['id']

        source = comment['subs'][0]
        target = comment['subs'][1]

        # get and check all ingredients of the recipe
        if source not in list(mutual_info_dict.keys()):
            alternative_found = False
            for ingredient_variants in comment["ingredients"]:
                if alternative_found:
                    break
                if source in ingredient_variants:
                    for ingredient_variant in ingredient_variants:
                        if ingredient_variant in list(mutual_info_dict.keys()):
                            source = ingredient_variant
                            alternative_found = True
                            break
            if not alternative_found:
                skipped_recipe_ids.append((recipe_id, source))
                continue

        recipe_ingredients = []
        for ingredient in comment['ingredients']:
            for ingr_variant in ingredient:
                if isinstance(ingr_variant, list):
                    for ingr_var_ in ingr_variant:
                        if ingr_var_ in mutual_info_dict:
                            ingr_variant = ingr_var_
                            recipe_ingredients.append(ingr_variant)
                    # if no variant was matched to the precalculated mutual info matrix, skip the ingredient
                    continue
                if ingr_variant in mutual_info_dict:
                    recipe_ingredients.append(ingr_variant)
                    break

        if len(recipe_ingredients) <= 0:
            skipped_recipe_ids.append(recipe_id)
            continue

        # rank all candidates based on their mutual info roles w.r.t. all other recipe ingredients
        recipe_ingredient_infos = []
        for ingredient in recipe_ingredients:
            ingredient_features = mutual_info_dict[ingredient]
            recipe_ingredient_infos.append(dict(sorted(ingredient_features.items())))

        # source_role_features = [mutual_infos[source] for mutual_infos in recipe_ingredient_infos]

        source_role_features = []
        for mutual_infos in recipe_ingredient_infos:
            if source in mutual_infos:
                source_role_features.append(mutual_infos[source])
            else:
                skipped_recipe_ids.append((recipe_id, source))
                break

        all_features = [list(mi.values()) for mi in recipe_ingredient_infos] # they just need to be transposed don't forget that
        all_ingredient_names = list(recipe_ingredient_infos[0].keys())

        sim_cosine = cosine_similarity

        if len(source_role_features) <= 0:
            skipped_recipe_ids.append((recipe_id, source))
            continue

        cosineDistances = getDistancesForTransposedLists(source_role_features, all_features, sim_cosine, None)
        cosineDistances_to_ingredients = list(zip(all_ingredient_names, cosineDistances))

        if recipe_id not in substitutabilities:
            substitutabilities[recipe_id] = {}
        if source not in substitutabilities[recipe_id]:
            substitutabilities[recipe_id][source] = {}
        substitutabilities[recipe_id][source][target] = cosineDistances_to_ingredients

    return substitutabilities, skipped_recipe_ids

def calc_all_coscine_substitutabilities(all_comments, mutual_info_dict):
    skipped_recipe_ids = []

    n_rows = len(all_comments) # every sample gets its own row
    n_cols = len(mutual_info_dict[list(mutual_info_dict.keys())[0]]) # all the ingredients for which we have precalced MIs (make sure they are the same everywhere)
    substitutabilities = torch.zeros(n_rows, n_cols, dtype=torch.double)

    sorted_columns = sorted(list(mutual_info_dict[list(mutual_info_dict.keys())[0]].keys()))
    ingr_to_col = {enum[1]: enum[0] for enum in enumerate(sorted_columns)}
    sample_to_row = {}

    row_index = 0

    ###

    # get results over all requested recipes
    for comment in all_comments:
        if row_index % 1000 == 0:
            print(row_index)

        recipe_id = comment['id']

        source = comment['subs'][0]
        target = comment['subs'][1]

        # get and check all ingredients of the recipe
        if source not in list(mutual_info_dict.keys()):
            alternative_found = False
            for ingredient_variants in comment["ingredients"]:
                if alternative_found:
                    break
                if source in ingredient_variants:
                    for ingredient_variant in ingredient_variants:
                        if ingredient_variant in list(mutual_info_dict.keys()):
                            source = ingredient_variant
                            alternative_found = True
                            break
            if not alternative_found:
                skipped_recipe_ids.append((recipe_id, source))
                continue

        recipe_ingredients = []
        for ingredient in comment['ingredients']:
            for ingr_variant in ingredient:
                if isinstance(ingr_variant, list):
                    for ingr_var_ in ingr_variant:
                        if ingr_var_ in mutual_info_dict:
                            ingr_variant = ingr_var_
                            recipe_ingredients.append(ingr_variant)
                    # if no variant was matched to the precalculated mutual info matrix, skip the ingredient
                    continue
                if ingr_variant in mutual_info_dict:
                    recipe_ingredients.append(ingr_variant)
                    break

        if len(recipe_ingredients) <= 0:
            skipped_recipe_ids.append(recipe_id)
            continue

        # rank all candidates based on their mutual info roles w.r.t. all other recipe ingredients
        recipe_ingredient_infos = []
        for ingredient in recipe_ingredients:
            ingredient_features = mutual_info_dict[ingredient]
            recipe_ingredient_infos.append(dict(sorted(ingredient_features.items())))

        # source_role_features = [mutual_infos[source] for mutual_infos in recipe_ingredient_infos]

        source_role_features = []
        for mutual_infos in recipe_ingredient_infos:
            if source in mutual_infos:
                source_role_features.append(mutual_infos[source])
            else:
                skipped_recipe_ids.append((recipe_id, source))
                break

        all_features = [list(mi.values()) for mi in recipe_ingredient_infos] # they just need to be transposed don't forget that
        all_ingredient_names = list(recipe_ingredient_infos[0].keys())

        sim_cosine = cosine_similarity

        if len(source_role_features) <= 0:
            skipped_recipe_ids.append((recipe_id, source))
            continue

        cosineDistances = getDistancesForTransposedLists(source_role_features, all_features, sim_cosine, None)
        cosine_distances_to_ingredients = list(zip(all_ingredient_names, cosineDistances))
        cosine_distances_per_ingredient = {k: v for k, v in sorted(cosine_distances_to_ingredients, key=lambda x: x[0])}

        val_tensor = torch.tensor(list(cosine_distances_per_ingredient.values()), dtype=torch.double)
        substitutabilities[row_index] = val_tensor

        if recipe_id not in sample_to_row:
            sample_to_row[recipe_id] = {}
        if source not in sample_to_row[recipe_id]:
            sample_to_row[recipe_id][source] = {}
        sample_to_row[recipe_id][source][target] = row_index
        row_index += 1

    return substitutabilities, ingr_to_col, sample_to_row, skipped_recipe_ids





if __name__ == "__main__":
    EXTENDED_RECIPES_PATH = os.path.abspath("./recipe1m/output/extended_recipes_with_quantities.json")
    PRECOMP_MI_PATH = os.path.abspath("./outputs/mutual_info_dict_with_self_info.pkl")

    MODEL_DATESETS_PATH = "./inputs/"
    TRAIN_COMMENTS_PATH = os.path.join(MODEL_DATESETS_PATH, "train_comments_subs.pkl")
    TEST_COMMENTS_PATH = os.path.join(MODEL_DATESETS_PATH, "test_comments_subs.pkl")
    VAL_COMMENTS_PATH = os.path.join(MODEL_DATESETS_PATH, "val_comments_subs.pkl")

    OUT_COS_SIM_PATH = os.path.abspath("./outputs/precalced_substitutabilities/cos_similarities.pkl")
    OUT_COS_SIM_TENSOR_PATH = os.path.abspath("./outputs/precalced_substitutabilities/cos_similarities.pt")
    SAMPLE_TO_COL_ROW = os.path.abspath("./outputs/precalced_substitutabilities/sample_2_row.pkl")
    INGR_TO_COL_PATH = os.path.abspath("./outputs/precalced_substitutabilities/ingr_2_col.pkl")
    SKIPPED_RECIPES_PATH = os.path.abspath("./outputs/precalced_substitutabilities/skipped_recipes.pkl")

    # with open(EXTENDED_RECIPES_PATH, 'r') as recipe_extended_with_original_info:
    #     extended_recipes = json.load(recipe_extended_with_original_info)
    # recipes_extended_dict = make_recipes_extended_dict(extended_recipes)


    all_comments = get_all_comments(TRAIN_COMMENTS_PATH, TEST_COMMENTS_PATH, VAL_COMMENTS_PATH)

    with open(PRECOMP_MI_PATH, "rb") as mutual_pi_file:
            mutual_info_dict = pickle.load(mutual_pi_file)


    # # * GISMo node names to verify that the info matrix and the recipes are as needed for GISMo
    # NODES_PATH = os.path.abspath("C:/UM/Master/FoodRecommendations/literature_models/GISMo/gismo/gismo/checkpoints/graph/nodes_191120.csv")
    # # node_id2count, node_count2id, node_id2name, node_name2id, ingredients_cnt, node_id2name, nnodes = load_gismo_node_data(NODES_PATH)
    # gismo_ingredient_names = load_gismo_ingredient_names(NODES_PATH)

    # # * checking for recipe extended dict if the sub sources are in the gismo node names
    # sub_source_not_in_gismo_nodes = []
    # sub_source_in_gismo_nodes = []
    # sub_source_variant_in_gismo_nodes = []
    # for recipe_id, recipe in list(recipes_extended_dict.items()):
    #     for sub in recipe['subs_collection']:
    #         sub_source = sub[0]


    #         if sub_source not in gismo_ingredient_names:
    #             alternative_found = False
    #             for ingredient_variants in recipe["ingredients"]:
    #                 if sub_source in ingredient_variants:
    #                     for ingredient_variant in ingredient_variants:
    #                         if ingredient_variant in gismo_ingredient_names:
    #                             sub_source = ingredient_variant
    #                             sub_source_variant_in_gismo_nodes.append(sub_source)
    #                             alternative_found = True
    #             if not alternative_found:
    #                 sub_source_not_in_gismo_nodes.append(sub_source)
    #         else:
    #             sub_source_in_gismo_nodes.append(sub_source)


    # print(len(sub_source_not_in_gismo_nodes))
    # s_test = set(sub_source_not_in_gismo_nodes)
    # print(s_test)



    # sub_source_not_in_gismo_nodes = []
    # sub_source_in_gismo_nodes = []
    # sub_source_variant_in_gismo_nodes = []
    # for recipe in all_comments:
    #     sub_source = recipe['subs'][0]
    #     sub_target = recipe['subs'][1]

    #     if sub_source not in mutual_info_dict:
    #         alternative_found = False
    #         for ingredient_variants in recipe["ingredients"]:
    #             if sub_source in ingredient_variants:
    #                 for ingredient_variant in ingredient_variants:
    #                     if ingredient_variant in mutual_info_dict:
    #                         sub_source = ingredient_variant
    #                         sub_source_variant_in_gismo_nodes.append(sub_source)
    #                         alternative_found = True
    #         if not alternative_found:
    #             sub_source_not_in_gismo_nodes.append(sub_source)
    #     else:
    #         sub_source_in_gismo_nodes.append(sub_source)


    # print(len(sub_source_not_in_gismo_nodes))
    # s_test = set(sub_source_not_in_gismo_nodes)
    # print(s_test)



    # # * if you want to check if the recipes_extended_dict has the same samples as all_comments
    # recipes_not_found = verify_recipe_data(recipes_extended_dict, alL_comments)

    # # * precalculate similarities as substitutability measure
    substitutabilities, ingr_to_col, sample_to_row, skipped_recipe_ids = calc_all_coscine_substitutabilities(all_comments, mutual_info_dict)


    # # * save the precalculated substitutabilities and skipped recipes
    with open(OUT_COS_SIM_PATH, "wb") as out_cos_sim_file:
        pickle.dump(substitutabilities, out_cos_sim_file)
    with open(INGR_TO_COL_PATH, "wb") as ingr_2_col_file:
        pickle.dump(ingr_to_col, ingr_2_col_file)
    with open(SAMPLE_TO_COL_ROW, "wb") as sample_2_row_file:
        pickle.dump(sample_to_row, sample_2_row_file)
    with open(SKIPPED_RECIPES_PATH, "wb") as skipped_recipes_file:
        pickle.dump(skipped_recipe_ids, skipped_recipes_file)

    torch.save(substitutabilities, OUT_COS_SIM_TENSOR_PATH)

    # ! TODO a better plan would be to use the numerica indices that we have from the all comments (each sample can be directly mapped, else we just use name and sub_source and sub_target to row dict + we have an ingr (from nodes) to ingr dict, then the table could be an efficient np array for easy storage, access and hopefully something that fits into memory!)

    # a = "dried_parsley" in mutual_info_dict
    # someshit = []
    # for fart, stuff in list(mutual_info_dict.items()):
    #     if "dried_parsley" not in stuff:
    #         pass
    #     if not isinstance(stuff, dict) or len(stuff) <= 0:
    #         someshit.append((fart, stuff))


    # print (list(stuff.keys()))
    # print(len(someshit))


    # for all the substitutions, generate some kind of probabilities per ingredient (set null or unavailable to 50-50)


    # finally create some vectors that can be easily used by the neural network dataset sampling to sample negatives (use two options: use more likeley positives vs use less likely postives more)


    print("ended")