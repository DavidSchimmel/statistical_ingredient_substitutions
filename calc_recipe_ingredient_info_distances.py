import pickle
import csv
import json
import os
import math
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances, manhattan_distances
from itertools import combinations


def get_graph_nodes(graph_nodes_path: str) -> list:
    """Load the data for node names for the flavorgraph nodes.

    Args:
        nodes_path (str): Nodes as they are in the flavorgraph

    Returns:
        list: The actual list of distinct node labels (i.e. ingredient labels)
    """
    graph_nodes = []
    with open(graph_nodes_path, 'r', newline='') as graph_nodes_file:
        csvreader = csv.reader(graph_nodes_file)
        columns = next(csvreader)
        for row in csvreader:
            if row[3] == "ingredient":
                graph_nodes.append(row[1])

    return graph_nodes


def get_all_gt_recipes(train_set_path, test_set_path, val_set_path, processed_recipes_path):
    if os.path.isfile(processed_recipes_path):
        with open(processed_recipes_path, "rb") as recipes_file:
            recipes = pickle.load(recipes_file)
            return recipes

    with open(train_set_path, "rb") as train_comments_file:
        train_comments = pickle.load(train_comments_file)
    with open(test_set_path, "rb") as test_comments_file:
        test_comments = pickle.load(test_comments_file)
    with open(val_set_path, "rb") as val_comments_file:
        val_comments = pickle.load(val_comments_file)

    all_comments = train_comments + test_comments + val_comments
    deep_recipes = [
        [comment["id"]] + comment["ingredients"] for comment in all_comments
    ]

    recipes = []
    recipe_ids_already_included = []

    for recipe in deep_recipes:
        if recipe[0] not in recipe_ids_already_included:
            shallow_recipe = []
            for ingredient in recipe:
                if isinstance(ingredient, list):
                    shallow_recipe += ingredient
                else:
                    shallow_recipe.append(ingredient)
            recipes.append(shallow_recipe)
            recipe_ids_already_included.append(recipe[0])

    with open(processed_recipes_path, "wb") as recipes_file:
        pickle.dump(recipes, recipes_file)

    return recipes#, all_comments


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

def get_1m_recipes(total_recipes_graph):
    with open(total_recipes_graph, 'r') as r1m_file:
        r1m_raw = json.load(r1m_file)

    return r1m_raw


def get_recipes_per_ingredient(ingredients, recipes, file_path):
    if os.path.isfile(file_path):
        with open(file_path, "rb") as recipes_file:
            recipes = pickle.load(recipes_file)
            return recipes

    i = 0
    recipes_per_ingredient = {}
    for ingredient in ingredients:
        i += 1
        k = 0
        recipes_per_ingredient[ingredient] = []
        for recipe in recipes:
            if k % 50000 == 0:
                print(f"ingredient number {i} recipe number {k}")
            k += 1
            if ingredient in recipe:
                recipes_per_ingredient[ingredient].append(recipe[0])
                continue

    with open(file_path, "wb") as recipes_file:
        pickle.dump(recipes_per_ingredient, recipes_file)

    return recipes_per_ingredient

def get_recipes_per_ingredient_pairs(recipes_per_ingredient, file_path):
    if os.path.isfile(file_path):
        with open(file_path, "rb") as recipes_file:
            recipes_per_ingredient_pairs = pickle.load(recipes_file)
            return recipes_per_ingredient_pairs

    recipes_per_ingredient_pairs = {}
    ingredient_combinations = list(combinations(list(recipes_per_ingredient.keys()), 2))
    i = 0

    for ingredient_pair in ingredient_combinations:
        intersection = list(set(recipes_per_ingredient[ingredient_pair[0]]) & set(recipes_per_ingredient[ingredient_pair[1]]))
        recipes_per_ingredient_pairs[ingredient_pair] = intersection
        i += 1
        if i % 1000000 == 0:
            print(i)

    with open(file_path, "wb") as recipes_file:
        pickle.dump(recipes_per_ingredient_pairs, recipes_file)
    return recipes_per_ingredient_pairs


def get_all_frequencies(recipes_per_ingredient,
                                recipes_per_ingredient_pairs):
    p_is = {
        ingredient: len(recipes)
        for ingredient, recipes in recipes_per_ingredient.items()
    }

    p_iks = {
        ingredient_pair: len(recipes)
        for ingredient_pair, recipes in recipes_per_ingredient_pairs.items()
    }

    # already_processed_pairs = list(p_iks.keys())
    # ingredients = list(recipes_per_ingredient.keys())
    # for ingredient_1 in ingredients:
    #     for ingredient_2 in ingredients:
    #         if (ingredient_1, ingredient_2) in already_processed_pairs or (
    #                 ingredient_2, ingredient_1) in already_processed_pairs:
    #             continue
    #         else:
    #             p_iks[(ingredient_1, ingredient_2)] = 0

    # p_iks = {}
    # ingredients = list(recipes_per_ingredient.keys())
    # for ingredient_1 in ingredients:
    #     for ingredient_2 in ingredients:
    #         if ingredient_1 == ingredient_2 or (ingredient_2,
    #                                             ingredient_1) in p_iks:
    #             continue
    #         ingredient_pair = (ingredient_1, ingredient_2)
    #         if ingredient_pair not in list(recipes_per_ingredient_pairs.keys()):
    #             ingredient_pair = (ingredient_2, ingredient_1)
    #         if ingredient_pair not in list(recipes_per_ingredient_pairs.keys()):
    #             p_iks[(ingredient_1, ingredient_2)] = 0
    #         else:
    #             p_iks[(ingredient_1, ingredient_2)] = len(
    #                 recipes_per_ingredient_pairs[ingredient_pair])
    return p_is, p_iks

def calc_mut_info_factor(p_1, p_2, p_1_2):
    if p_1 == 0 or p_2 == 0 or p_1_2 == 0:
        return 0

    factor = p_1_2 * math.log(p_1_2 / (p_1 * p_2))
    return factor


def get_recipe_ingredient_df(ingredients, recipes, recipes_per_ingredient, file_path):
    """Calculate a one-hot dataframe where a recipe row and ingredient col is 1 iff the
    ingredient is contained in the recipe. Always takes the first ingredient if the
    recipe ingredient is a list of more than one variant of the ingredient label.

    Args:
        ingredients (_type_): _description_
        recipes (_type_): _description_
        recipes_per_ingredient (_type_): _description_
        file_path (_type_): _description_

    Returns:
        _type_: _description_
    """
    if os.path.isfile(file_path):
        with open(file_path, "rb") as recipes_file:
            df = pickle.load(recipes_file)
            return df

    recipe_ids = [recipe[0] for recipe in recipes]
    data = [[0 for _ in ingredients] for _ in recipe_ids]
    df = pd.DataFrame(data, columns=ingredients, index=recipe_ids)

    for ingredient, recipes in recipes_per_ingredient.items():
        for recipe_id in recipes:
            df.loc[recipe_id, ingredient] = 1

    with open(file_path, "wb") as recipes_file:
        pickle.dump(df, recipes_file)
    return df

def get_all_pairs(df, file_path):
    if os.path.isfile(file_path):
        with open(file_path, "rb") as file:
            all_pairs = pickle.load(file)
            return all_pairs

    cols = df.columns
    all_pairs = []
    for i in range(len(cols)):
        for k in range(i, len(cols)):
            all_pairs.append((cols[i], cols[k]))

    with open(file_path, "wb") as file:
        pickle.dump(all_pairs, file)
    return all_pairs

def get_all_mutual_info(recipe_ingredient_df_bool, file_path):
    # load da file if available
    mutual_info_dict = None
    if os.path.isfile(file_path):
        with open(file_path, "rb") as file:
            mutual_info_dict = pickle.load(file)

    # get cols in reverse order (i.e. ingredients)
    ingredient_list = list(reversed(recipe_ingredient_df_bool.columns))

    # get ingredients that already exists as keys
    if mutual_info_dict is not None:
        existing_ingredients_set = set(mutual_info_dict.keys())
        open_ingredient_list = list(set(ingredient_list) - existing_ingredients_set)
    else:
        open_ingredient_list = ingredient_list


    # iterate the reversed column list and calc mut info if not in the dict already
    for i, ingredient in enumerate(open_ingredient_list):
        # calculate mutual information of the ingredient with all other ingredients
        ingredient_mutual_information = get_mutual_infos_for_ingredient(ingredient, recipe_ingredient_df_bool)
        mutual_info_dict[ingredient] = ingredient_mutual_information

        # every 20th step, save the dict
        if i % 100 == 0:
            with open(file_path, "wb") as file:
                pickle.dump(mutual_info_dict, file)

    with open(file_path, "wb") as file:
        pickle.dump(mutual_info_dict, file)
    return mutual_info_dict


def get_mutual_infos_for_ingredient(ingredient, recipe_ingredient_df):
    df = recipe_ingredient_df.astype(bool)

    # Remove the target column from the DataFrame to get the features
    if (ingredient not in list(df.columns)):
        return {}
    features = df.drop(ingredient, axis=1)
    features_integers = features.astype(int)
    # Calculate mutual information for the selected target column and other columns
    mi_values = mutual_info_classif(features_integers, df[ingredient], discrete_features=True)

    # Create a dictionary mapping columns to their corresponding mutual information values
    mi_dict = {col: mi for col, mi in zip(features.columns, mi_values)}

    direct_mutual_info_sorted = dict(sorted(mi_dict.items(), key=lambda item: item[1], reverse=True))

    return direct_mutual_info_sorted

def add_self_information_to_all_mutual_info (mutual_info_dict_path, mutual_info_dict_with_self_info_path):
    if os.path.isfile(mutual_info_dict_path):
        with open(mutual_info_dict_path, "rb") as file:
            mutual_info_dict = pickle.load(file)

    for key, val in mutual_info_dict.items():
        test = key in list(val.keys())
        test2 = key in list(mutual_info_dict[key].keys())
        mutual_info_dict[key][key] = 0
        test3 = key in list(mutual_info_dict[key].keys())

    with open(mutual_info_dict_with_self_info_path, "wb") as file:
        pickle.dump(mutual_info_dict, file)
    return mutual_info_dict

def test_for_recipe(recipe_id, recipes, recipe_ingredient_df_bool, file_path):
    mutual_info_dict = {}

    #load the existing one if there is one
    if os.path.isfile(file_path):
        with open(file_path, "rb") as file:
            mutual_info_dict = pickle.load(file)


    recipe = None
    for r in recipes:
        if r["id"] == recipe_id:
            recipe = r
            break

    if recipe == None:
        return "None"
    source_ingredient, target_ingredient = recipe["subs"]
    other_recipe_ingredients = recipe["ingredients"]

    # for the source ingredient
    if (source_ingredient not in mutual_info_dict):
        source_mutual_info = get_mutual_infos_for_ingredient(source_ingredient, recipe_ingredient_df_bool)
        mutual_info_dict[source_ingredient] = source_mutual_info
    else:
        source_mutual_info = mutual_info_dict[source_ingredient]

    # for the target ingredient
    if (target_ingredient not in mutual_info_dict):
        target_mutual_info = get_mutual_infos_for_ingredient(target_ingredient, recipe_ingredient_df_bool)
        mutual_info_dict[target_ingredient] = target_mutual_info
    else:
        target_mutual_info = mutual_info_dict[target_ingredient]

    # for all other recipe ingredients
    for recipe_ingredient_array in other_recipe_ingredients:
        recipe_ingredient = recipe_ingredient_array[0]
        if (recipe_ingredient not in list(recipe_ingredient_df_bool.columns)):
            continue
        if (recipe_ingredient not in mutual_info_dict):
            recipe_ingredient_mutual_info = get_mutual_infos_for_ingredient(recipe_ingredient, recipe_ingredient_df_bool)
            mutual_info_dict[recipe_ingredient] = recipe_ingredient_mutual_info
        else:
            recipe_ingredient_mutual_info = mutual_info_dict[recipe_ingredient]

    with open(file_path, "wb") as file:
        pickle.dump(mutual_info_dict, file)

    print("done")




def getRecipeRecommendations(recipe_id, extended_recipes, recipe_ingredient_df_bool, precalculated_mutual_info_dict, ):

    for recipe in extended_recipes:
        if recipe["id"] == recipe_id:

            source_ingredient = recipe["subs"][0]
            target_ingredient = recipe["subs"][1]
            recipe_ingredients = []
            for ingredient in recipe["ingredients"]:
                if (ingredient[0] == source_ingredient):
                    continue
                recipe_ingredients.append(ingredient[0])
            break

    # don't check if all required ingredients are in the df columns yet, because we don't make automatic computations
    # also don't check for all 0 mutual intelligence entries

    # this is needed for the direct MI recommendations
    if (source_ingredient in list(precalculated_mutual_info_dict.keys())):
        source_mutual_infos = precalculated_mutual_info_dict[source_ingredient]
    else:
        source_mutual_infos = get_mutual_infos_for_ingredient(source_ingredient, recipe_ingredient_df_bool)

    sorted_source_mutual_infos = dict(sorted(source_mutual_infos.items(), key=lambda item: item[1], reverse=True))
    gt_rank_direct_mi_recommenation = 0
    for i, item in enumerate(sorted_source_mutual_infos.items()):
        if item[0] == target_ingredient:
            gt_rank_direct_mi_recommenation = i
            if item[1] == 0:
                return 0,0,[]
            break


    recipe_ingredient_features = []
    for ingredient in recipe_ingredients:
        if (ingredient in list(precalculated_mutual_info_dict.keys())):
            ingredient_features = precalculated_mutual_info_dict[ingredient]
        else:
            ingredient_features = get_mutual_infos_for_ingredient(ingredient, recipe_ingredient_df_bool)
        recipe_ingredient_features.append(dict(sorted(ingredient_features.items())))

    source_features = [mutual_infos[source_ingredient] for mutual_infos in recipe_ingredient_features]
    all_features = [list(mi.values()) for mi in recipe_ingredient_features]
    all_ingredient_names = list(recipe_ingredient_features[0].keys())

    dist_euclidean = euclidean_distances
    distances = getDistancesForTransposedLists(source_features, all_features, dist_euclidean)

    # similarities_to_ingredients = zip(all_ingredient_names, similarities)
    # recommendations_sorted = sorted(similarities_to_ingredients, key=lambda x: x[1], reverse=True)
    distances_to_ingredients = zip(all_ingredient_names, distances)
    recommendations_sorted = sorted(distances_to_ingredients, key=lambda x: x[1])

    gt_rank_in_similarities = 0
    for i, ingredient_similarity_pair in enumerate(recommendations_sorted):
        if (ingredient_similarity_pair[0] == target_ingredient):
            gt_rank_in_similarities = i
            break


    return gt_rank_direct_mi_recommenation, gt_rank_in_similarities, recommendations_sorted

def collectSomeRecipeRecommendations(recipe_ids, extended_recipes, recipe_ingredient_df_bool, mutual_info_dict):
    some_gt_rank_direct_mi_recommenation = []
    some_gt_rank_in_similarities = []

    limit = 280 if len(recipe_ids) > 280 else len(recipe_ids)

    for i, recipe_id in enumerate(recipe_ids):
        if i in [155, 186, 201, 213, 253]:
            continue # dried parsley??
        if i > limit:
            break
        gt_rank_direct_mi_recommenation, gt_rank_in_similarities, similarieties_recommendations_sorted = getRecipeRecommendations(recipe_id, extended_recipes, recipe_ingredient_df_bool, mutual_info_dict)
        some_gt_rank_direct_mi_recommenation.append(gt_rank_direct_mi_recommenation)
        some_gt_rank_in_similarities.append(gt_rank_in_similarities)
    return some_gt_rank_direct_mi_recommenation, some_gt_rank_in_similarities



def getRecommendationsBasedOnMutualInformationRole(recipe_ids, extended_recipes, mutual_info_dict, normalization=None, limiter_indiv_ingr_distance=None):
    extended_recipes_dict = {recipe["id"]: recipe for recipe in extended_recipes}

    skipped_recipe_ids = []
    direct_source_mutual_info_recommendations = {}
    cosine_similarity_role_recommendations = {}
    euclidean_similarity_role_recommendations = {}
    manhatten_similarity_role_recommendations = {}

    # get results over all requested recipes
    for recipe_id in recipe_ids:
        # get the corresponding recipe from the comments, skip if it cannot be found
        if recipe_id not in list(extended_recipes_dict.keys()):
            skipped_recipe_ids.append(recipe_id)
            continue
        recipe = extended_recipes_dict[recipe_id]

        # get and check all ingredients of the recipe

        if recipe["subs"][0] not in list(mutual_info_dict.keys()):
            skipped_recipe_ids.append(recipe_id)
        else:
            source = recipe["subs"][0]

        if recipe["subs"][1] not in list(mutual_info_dict.keys()):
            skipped_recipe_ids.append(recipe_id)
        else:
            target = recipe["subs"][1]

        recipe_ingredients = []
        not_all_ingredients_are_precalced = False
        for ingredient_variants in recipe["ingredients"]:
            ingredient = None
            for ingredient_variant in ingredient_variants:
                if ingredient_variant in list(mutual_info_dict.keys()):
                    ingredient = ingredient_variant
                    recipe_ingredients.append(ingredient)
                    break
            if ingredient is None:
                not_all_ingredients_are_precalced = True
                break
            # if ingredient not in list(mutual_info_dict.keys()):
            #     not_all_ingredients_are_precalced = True
            #     break
            # else:
            #     recipe_ingredients.append(ingredient)
        if not_all_ingredients_are_precalced:
            skipped_recipe_ids.append(recipe_id)
            continue

        # calculate direct co-similarities from source to all targets to rank the candidates
        source_mutual_infos = mutual_info_dict[source]
        sorted_source_mutual_infos = dict(sorted(source_mutual_infos.items(), key=lambda item: item[1], reverse=True))
        direct_source_mutual_info_recommendations[recipe_id] = sorted_source_mutual_infos

        # rank all candidates based on their mutual info roles w.r.t. all other recipe ingredients
        recipe_ingredient_infos = []
        for ingredient in recipe_ingredients:
            ingredient_features = mutual_info_dict[ingredient]
            recipe_ingredient_infos.append(dict(sorted(ingredient_features.items())))

        source_role_features = [mutual_infos[source] for mutual_infos in recipe_ingredient_infos]
        all_features = [list(mi.values()) for mi in recipe_ingredient_infos] # they just need to be transposed don't forget that
        all_ingredient_names = list(recipe_ingredient_infos[0].keys())


        # out_of_order_ingredients = []
        # #check the ingredient names for all vectors in order
        # for i in range(len(all_ingredient_names)):
        #     for rece in recipe_ingredient_infos:
        #         if all_ingredient_names[i] != list(rece.keys())[i]:
        #             print(all_ingredient_names[i], " - ", list(rece.keys())[i])
        #             out_of_order_ingredients.append(all_ingredient_names[i])

        # calculate distances/similarieties and get recommendations
        if limiter_indiv_ingr_distance == None:
            sim_cosine = cosine_similarity
            cosineDistances = getDistancesForTransposedLists(source_role_features, all_features, sim_cosine, normalization)
            cosineDistances_to_ingredients = zip(all_ingredient_names, cosineDistances)
            cosine_recommendations_sorted = sorted(cosineDistances_to_ingredients, key=lambda x: x[1], reverse=True)
            cosine_similarity_role_recommendations[recipe_id] = cosine_recommendations_sorted

            dist_euclidean = euclidean_distances
            euclideanDistances = getDistancesForTransposedLists(source_role_features, all_features, dist_euclidean, normalization)
            euclideanDistances_to_ingredients = zip(all_ingredient_names, euclideanDistances)
            euclidean_recommendations_sorted = sorted(euclideanDistances_to_ingredients, key=lambda x: x[1])
            euclidean_similarity_role_recommendations[recipe_id] = euclidean_recommendations_sorted

            dist_manhatten = manhattan_distances
            manhattenDistances = getDistancesForTransposedLists(source_role_features, all_features, dist_manhatten, normalization)
            manhattenDistances_to_ingredients = zip(all_ingredient_names, manhattenDistances)
            manhatten_recommendations_sorted = sorted(manhattenDistances_to_ingredients, key=lambda x: x[1])
            manhatten_similarity_role_recommendations[recipe_id] = manhatten_recommendations_sorted

        else:
            sim_cosine = cosine_similarity
            cosineDistances = getDistancesForTransposedListsWithIndivLimiter(source_role_features, all_features, sim_cosine, normalization, limiter_indiv_ingr_distance)
            cosineDistances_to_ingredients = zip(all_ingredient_names, cosineDistances)
            cosine_recommendations_sorted = sorted(cosineDistances_to_ingredients, key=lambda x: x[1], reverse=True)
            cosine_similarity_role_recommendations[recipe_id] = cosine_recommendations_sorted

            dist_euclidean = euclidean_distances
            euclideanDistances = getDistancesForTransposedListsWithIndivLimiter(source_role_features, all_features, dist_euclidean, normalization, limiter_indiv_ingr_distance)
            euclideanDistances_to_ingredients = zip(all_ingredient_names, euclideanDistances)
            euclidean_recommendations_sorted = sorted(euclideanDistances_to_ingredients, key=lambda x: x[1])
            euclidean_similarity_role_recommendations[recipe_id] = euclidean_recommendations_sorted

            dist_manhatten = manhattan_distances
            manhattenDistances = getDistancesForTransposedListsWithIndivLimiter(source_role_features, all_features, dist_manhatten, normalization, limiter_indiv_ingr_distance)
            manhattenDistances_to_ingredients = zip(all_ingredient_names, manhattenDistances)
            manhatten_recommendations_sorted = sorted(manhattenDistances_to_ingredients, key=lambda x: x[1])
            manhatten_similarity_role_recommendations[recipe_id] = manhatten_recommendations_sorted

    return direct_source_mutual_info_recommendations, cosine_similarity_role_recommendations, euclidean_similarity_role_recommendations, manhatten_similarity_role_recommendations


def getDistancesForTransposedLists(source_features, all_features, distance, normalization=None):
    reference_vector = np.array(source_features).reshape(1, -1)
    other_vectors = np.transpose(np.array(all_features))

    if normalization is not None:
        if normalization == "dampen_square":
            reference_vector = np.power(reference_vector, 2)
            other_vectors = np.power(other_vectors, 2)
        if normalization == "minmax":
            ref_mini = reference_vector.min()
            ref_maxi = reference_vector.max()
            other_mini = reference_vector.min()
            other_maxi = reference_vector.max()
            mini = min([ref_mini, other_mini])
            maxi = max([ref_maxi, other_maxi])

            reference_vector = (reference_vector - mini) / (maxi - mini)
            other_vectors = (other_vectors - mini) / (maxi - mini)

    similarity_matrix = distance(reference_vector, other_vectors)
    return similarity_matrix[0].tolist()


def getDistancesForTransposedListsWithIndivLimiter(source_features, all_features, distance, normalization=None, limiter=None):
    reference_vector = np.array(source_features).reshape(1, -1)
    other_vectors = np.transpose(np.array(all_features))

    if normalization is not None:
        if normalization == "dampen_square":
            reference_vector = np.power(reference_vector, 2)
            other_vectors = np.power(other_vectors, 2)
        if normalization == "minmax":
            ref_mini = reference_vector.min()
            ref_maxi = reference_vector.max()
            other_mini = reference_vector.min()
            other_maxi = reference_vector.max()
            mini = min([ref_mini, other_mini])
            maxi = max([ref_maxi, other_maxi])

            reference_vector = (reference_vector - mini) / (maxi - mini)
            other_vectors = (other_vectors - mini) / (maxi - mini)

    if distance == cosine_similarity:
        distances = similarity_matrix = distance(reference_vector, other_vectors)[0].tolist()

    elif distance == euclidean_distances:
        element_wise_distances = other_vectors - reference_vector
        element_wise_distances = element_wise_distances ** 2

        if limiter == "squared":
            element_wise_distances = element_wise_distances ** 2
        if limiter == "factor":
            element_wise_distances = element_wise_distances * 0.5
        if limiter == "frequency_weights":
            pass ## TODO implement this

        distances_squared = np.sum(element_wise_distances, axis=1)
        distances = np.sqrt(distances_squared)
    elif distance == manhattan_distances:
        element_wise_distances = np.abs(other_vectors - reference_vector)

        if limiter== "squared":
            element_wise_distances = element_wise_distances ** 2
        if limiter == "factor":
            element_wise_distances = element_wise_distances * 0.5
        if limiter == "frequency_weights":
            pass ## TODO implement this

        distances = np.sum(element_wise_distances, axis=1)

    return distances



def getCosineDistances():
    def cosine_similarity_matrix(reference_vector, other_vectors):
        reference_vector = np.array(reference_vector).reshape(1, -1)
        other_vectors = np.array(other_vectors)
        useless = np.transpose(other_vectors)
        similarity_matrix = cosine_similarity(reference_vector, other_vectors)
        return similarity_matrix[0]

    reference_vector = [1.0, 2.0, 3.0]
    other_vectors = [
        [4.0, 5.0, 6.0],
        [0.0, 1.0, 2.0],
        [2.0, 3.0, 4.0],
        [1.0, 2.0, 3.0]
    ]

    similarity_matrix = cosine_similarity_matrix(reference_vector, other_vectors)
    print("Cosine Similarity Matrix:")
    print(similarity_matrix)


def evalRecommendations(direct_ranks, similarities_ranks):
    similarities_rank_count = 0
    direct_rank_count = 0
    indif_count = 0
    rank_diffs = [] # calc rank by direct_ranks - similarities_ranks, i.e. the higher the scpre, the better was the good_maybe rank
    for direct_rank, similarities_rank in zip(direct_ranks, similarities_ranks):
        if direct_rank > similarities_rank + 10:
            similarities_rank_count += 1
        elif similarities_rank > direct_rank + 10:
            direct_rank_count += 1
        else:
            indif_count += 1
        rank_diffs.append(direct_rank - similarities_rank)

    average_ranking_diff = sum(rank_diffs) / len(rank_diffs)

    print(f"nr of times the similarity based score was better: {similarities_rank_count}\n number of times the direct MI was better: {direct_rank_count}\n indiffernet: {indif_count}\n ranking diff (the higher the more is the average in favour of similarities) {average_ranking_diff}")


def getNaiveBayesRecommendations(recipe_ids, extended_recipes, ingredient_recipe_counts, pairwise_ingredient_recipe_counts):
    extended_recipes_dict = {recipe["id"]: recipe for recipe in extended_recipes}

    recipe_recommendations = {}
    for recipe_id in recipe_ids:
        if recipe_id not in list(extended_recipes_dict.keys()):
            continue

        # filter the source ingredient form the recipe
        recipe = extended_recipes_dict[recipe_id]
        source_ingr = recipe["subs"][0]
        recipe_ingredients = [ingr[0] for ingr in recipe["ingredients"] if ingr[0] != source_ingr]

        ingredient_likelyhoods = {}
        # for all possible ingredients, calculate the likelyhood that it fits to the other recipe ingredients
        for query_ingredient, ingredient_recipe_count in ingredient_recipe_counts.items():
            # if the ingredient has a frequency of zero, the likelyhood is zero
            p_ingr = 0
            if query_ingredient not in list(ingredient_recipe_counts.keys()) or ingredient_recipe_count == 0:
                ingredient_likelyhoods[query_ingredient] = 0
                continue

            ingredient_likelyhood = ingredient_recipe_count
            # otherwise calculate ingredient likelyhood based on the naive bayesian filtering
            for recipe_ingredient in recipe_ingredients:
                if recipe_ingredient not in list(ingredient_recipe_counts.keys())or ingredient_recipe_counts[recipe_ingredient] == 0:
                    continue # if the denominator is 0, we assume the term will be 1
                else:
                    denominator = ingredient_recipe_counts[recipe_ingredient]
                if (recipe_ingredient, query_ingredient) in pairwise_ingredient_recipe_counts:
                    factor = pairwise_ingredient_recipe_counts[(recipe_ingredient, query_ingredient)]
                elif (query_ingredient, recipe_ingredient) in pairwise_ingredient_recipe_counts:
                    factor = pairwise_ingredient_recipe_counts[(query_ingredient, recipe_ingredient)]
                else:
                    factor = 0
                if factor == 0:
                    factor = 0.0001 # set small offset to avoid invalidation because of missing data
                ingredient_likelyhood *= factor / denominator

            ingredient_likelyhoods[query_ingredient] = ingredient_likelyhood
        ingredient_likelyhoods_sorted = dict(sorted(ingredient_likelyhoods.items(), key=lambda item: item[1], reverse=True))
        recipe_recommendations[recipe_id] = ingredient_likelyhoods_sorted

    return recipe_recommendations


def main():
    USE_ONLY_COMMENTS_RECIPES = True

    TRAIN_COMMENTS_PATH = os.path.abspath("./inputs/train_comments_subs.pkl") # train recipes with substitutions
    TEST_COMMENTS_PATH = os.path.abspath("./inputs/test_comments_subs.pkl") # test recipes with substitutions
    VAL_COMMENTS_PATH = os.path.abspath("./inputs/val_comments_subs.pkl") # validation recipes with substitutions
    GRAPH_NODES_PATH = os.path.abspath("./inputs/graph/nodes_191120.csv")

    RECIPE1M_PATH = os.path.abspath("./inputs/layer1.json") #currently not needed

    # ALL_PAIRS_PATH = os.path.abspath("./outputs/all_pairs.pkl")
    # ALL_MUTUAL_INFO_PATH = os.path.abspath("./outputs/all_mutual_info.pkl")
    EXTENDED_RECIPES_PATH = os.path.abspath("./inputs/extended_recipes.pkl")

    MUTUAL_INFO_DICT_PATH = "./outputs/mutual_info_dict.pkl"
    MUTUAL_INFO_DICT_PATH_WITH_SELF_INFO = "./outputs/mutual_info_dict_with_self_info.pkl"

    ORDERED_RECIPE_IDS_PATH = os.path.abspath("./outputs/sorted_recipe_ids_list.pkl") # this can probably be ignored for now, that was just to have some sample recipe ids


    # get nodes and recipes
    ingredients = get_graph_nodes(GRAPH_NODES_PATH)

    if (USE_ONLY_COMMENTS_RECIPES):
        RECIPES_PER_INGREDIENT_SMALL_PATH = os.path.abspath(
            "./outputs/recipes_per_ingredient_small.pkl"
        )
        RECIPES_PER_INGREDIENT_PAIRS_SMALL_PATH = os.path.abspath(
            "./outputs/recipes_per_ingredient_pairs_small.pkl"
        )
        PROCESSED_RECIPES_PATH = os.path.abspath(
            "./outputs/processed_recipes.pkl"
        )

        recipes = get_all_gt_recipes(TRAIN_COMMENTS_PATH, TEST_COMMENTS_PATH,
                                     VAL_COMMENTS_PATH, PROCESSED_RECIPES_PATH)
        recipes_per_ingredient = get_recipes_per_ingredient(
            ingredients, recipes, RECIPES_PER_INGREDIENT_SMALL_PATH)

        test = recipes_per_ingredient["pineapple_juice"]

        recipes_per_ingredient_pairs = get_recipes_per_ingredient_pairs(
            recipes_per_ingredient, RECIPES_PER_INGREDIENT_PAIRS_SMALL_PATH)
        recipe_ingredient_counts, recipe_ingredient_pair_counts = get_all_frequencies(recipes_per_ingredient,
                                              recipes_per_ingredient_pairs)


        INGREDIENT_RECIPE_MATRIX_PATH = os.path.abspath(
            "./outputs/ingredient_recipe_matrix.pkl"
        )
        recipe_ingredient_df = get_recipe_ingredient_df(
            ingredients, recipes, recipes_per_ingredient, INGREDIENT_RECIPE_MATRIX_PATH)

        #### this could be interersting part of analysis, checking which ingredient appears only once in a recipe
        # for column in recipe_ingredient_df.columns:
        #     value_counts = recipe_ingredient_df[column].value_counts()
        #     print(f"Value counts for {column}:\n{value_counts}\n")

        ##### this one is important
        # all_pairs = get_all_pairs(recipe_ingredient_df, ALL_PAIRS_PATH)

        ##### this one is important
        # all_mutual_info = get_all_mutual_info(all_pairs, recipe_ingredient_df, ALL_MUTUAL_INFO_PATH)

        extended_recipes = get_all_comments(TRAIN_COMMENTS_PATH, TEST_COMMENTS_PATH,
                                     VAL_COMMENTS_PATH, EXTENDED_RECIPES_PATH)
        # make bool to make the computation faster
        recipe_ingredient_df_bool = recipe_ingredient_df.astype(bool)
        # test_for_recipe("b78b1bffd0", extended_recipes, recipe_ingredient_df_bool, MUTUAL_INFO_DICT_PATH)


        CONTINUE_GETTING_MORE_MUTUL_INFO = False
        if CONTINUE_GETTING_MORE_MUTUL_INFO:
            all_mutual_info = get_all_mutual_info(recipe_ingredient_df_bool, MUTUAL_INFO_DICT_PATH)

        Add_SELF_INFO_TO_MUTUAL_INFO_DICT = False
        if Add_SELF_INFO_TO_MUTUAL_INFO_DICT:
            mutual_info_dict = add_self_information_to_all_mutual_info(MUTUAL_INFO_DICT_PATH, MUTUAL_INFO_DICT_PATH_WITH_SELF_INFO)


        if os.path.isfile(ORDERED_RECIPE_IDS_PATH):
            with open(ORDERED_RECIPE_IDS_PATH, "rb") as file:
                ordered_recipe_ids = pickle.load(file)
        recipe_ids_with_ranks = ordered_recipe_ids
        ordered_recipe_ids = [recipe[1] for recipe in recipe_ids_with_ranks]

        CONTINUE_ENCODING_RECIPES = False
        if CONTINUE_ENCODING_RECIPES:

            for i, recipe_id in enumerate(ordered_recipe_ids):
                pass
                # test_for_recipe(recipe_id, extended_recipes, recipe_ingredient_df_bool, MUTUAL_INFO_DICT_PATH)


        ### get naive bayes recommendations
        DO_CALC_NAIVE_BAYES_RECOMMENDATIONS = False
        if DO_CALC_NAIVE_BAYES_RECOMMENDATIONS:
            naive_bayes_recommendations = getNaiveBayesRecommendations(["7f000ac3af"], extended_recipes, recipe_ingredient_counts, recipe_ingredient_pair_counts)

        # getCosineDistances()

        if os.path.isfile(MUTUAL_INFO_DICT_PATH_WITH_SELF_INFO):
            with open(MUTUAL_INFO_DICT_PATH_WITH_SELF_INFO, "rb") as file:
                mutual_info_dict = pickle.load(file)
        test = getRecommendationsBasedOnMutualInformationRole(["7f000ac3af", "a24d9d2dc7", "cdb4516b34", "c8633ab596", "522d574efd", "c9b44e6c70", "a21302e305", "6c44d67ae5", "fce4d48e89"], extended_recipes, mutual_info_dict, None, "squared")

        # recipe_id = "b78b1bffd0"
        # recipe_recommendations = getRecipeRecommendations(recipe_id, extended_recipes, recipe_ingredient_df_bool, mutual_info_dict)

        direct_counts, similarities_count = collectSomeRecipeRecommendations(ordered_recipe_ids, extended_recipes, recipe_ingredient_df_bool, mutual_info_dict)
        evalRecommendations(direct_counts, similarities_count)

        some_well_predicted_recipe_ids = ["7f000ac3af", "a24d9d2dc7", "cdb4516b34", "c8633ab596", "522d574efd", "c9b44e6c70", "a21302e305", "6c44d67ae5", "fce4d48e89"]
        direct_counts, similarities_count = collectSomeRecipeRecommendations(some_well_predicted_recipe_ids, extended_recipes, recipe_ingredient_df_bool, mutual_info_dict)
        evalRecommendations(direct_counts, similarities_count)

        # good_count = 0
        # bad_count = 0
        # indif_count = 0
        # rank_diffs = [] # calc rank by bad_maybe - good_maybe, i.e. the higher the scpre, the better was the good_maybe rank
        # for bad, good in zip(bad_maybe, good_maybe):
        #     if bad > good + 10:
        #         good_count += 1
        #     elif good > bad + 10:
        #         bad_count += 1
        #     else:
        #         indif_count += 1
        #     rank_diffs.append(bad - good)

        # average_ranking_diff = sum(rank_diffs) / len(rank_diffs)

        # print(f"nr of times the similarity based score was better: {good_count}\n number of times the direct MI was better: {bad_count}\n indiffernet: {indif_count}\n ranking diff (the higher the more is the average in favour of similarities) {average_ranking_diff}")



    else:
        recipes = get_1m_recipes(RECIPE1M_PATH)

    return


if __name__ == "__main__":
    main()

