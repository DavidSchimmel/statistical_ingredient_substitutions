import csv
import os
import pickle
import random
from pathlib import Path


from fuzzywuzzy import process

PATH_SURVEY_SAMPLES_WITH_ANSWERS = os.path.abspath("./survey_results_processed/survey_samples_with_answers.pkl")
PATH_IN_GISMO_TRAIN = os.path.abspath("./inputs/train_comments_subs.pkl")
PATH_IN_GISMO_TEST = os.path.abspath("./inputs/test_comments_subs.pkl")
PATH_IN_GISMO_VAL = os.path.abspath("./inputs/val_comments_subs.pkl")
PATH_OUT_ARCELIK_ONLY_TRAIN = os.path.abspath("./outputs/new_comments/arcelik_only/train_comments_subs.pkl")
PATH_OUT_ARCELIK_ONLY_TEST = os.path.abspath("./outputs/new_comments/arcelik_only/test_comments_subs.pkl")
PATH_OUT_ARCELIK_ONLY_VAL = os.path.abspath("./outputs/new_comments/arcelik_only/val_comments_subs.pkl")
PATH_OUT_ARCELIK_UNSEEN_TRAIN = os.path.abspath("./outputs/new_comments/arcelik_unseen/train_comments_subs.pkl")
PATH_OUT_ARCELIK_UNSEEN_TEST = os.path.abspath("./outputs/new_comments/arcelik_unseen/test_comments_subs.pkl")
PATH_OUT_ARCELIK_UNSEEN_VAL = os.path.abspath("./outputs/new_comments/arcelik_unseen/val_comments_subs.pkl")
PATH_OUT_ARCELIK_FIFE_FOLD_DIR = os.path.abspath("./outputs/new_comments/arcelik_five_fold/")
# PATH_OUT_ARCELIK_FILTERED_TRAIN = os.path.abspath("./outputs/new_comments/falvorgraph_appended/train_comments_subs.pkl")
# PATH_OUT_ARCELIK_FILTERED_TEST = os.path.abspath("./outputs/new_comments/falvorgraph_appended/test_comments_subs.pkl")
# PATH_OUT_ARCELIK_FILTERED_VAL = os.path.abspath("./outputs/new_comments/falvorgraph_appended/val_comments_subs.pkl")
NODES_PATH = os.path.abspath("./inputs/graph/nodes_191120.csv")

MATCH_THRESHOLD = 0.90

# how to dead with recipes where with negative fit?

def loadFlavourgraphIngrNodes(flavourgraph_nodes_path):
    graph_nodes = []
    with open(flavourgraph_nodes_path, 'r', newline='') as graph_nodes_file:
        csvreader = csv.reader(graph_nodes_file)
        _columns = next(csvreader)
        for row in csvreader:
            if row[3] == "ingredient":
                graph_nodes.append(row)
    return graph_nodes

def loadSurveySamplesWithAnswers():
    with open(PATH_SURVEY_SAMPLES_WITH_ANSWERS, "rb") as survey_file:
        survey_samples_with_answers = pickle.load(survey_file)
    return survey_samples_with_answers

def loadGismoSplits():
    with open(PATH_IN_GISMO_TRAIN, "rb") as train_file:
        gismo_train = pickle.load(train_file)
    with open(PATH_IN_GISMO_VAL, "rb") as val_file:
        gismo_val = pickle.load(val_file)
    with open(PATH_IN_GISMO_TEST, "rb") as test_file:
        gismo_test = pickle.load(test_file)
    return gismo_train, gismo_val, gismo_test

def generateArcelikPureSplits(all_comments):
    train_comments = []
    val_comments = []
    test_comments = []

    alt_counter = 0
    subs_counters = {}

    for comment in all_comments:
        if comment["subs"] not in list(subs_counters.keys()):
            subs_counters[comment["subs"]] = 0
        subs_counters[comment["subs"]] += 1
        if subs_counters[comment["subs"]] <= 5:
            train_comments.append(comment)
        elif subs_counters[comment["subs"]] == 6:
            test_comments.append(comment)
        elif subs_counters[comment["subs"]] == 7:
            val_comments.append(comment)
        else:
            alt_counter += 1
            if alt_counter <= 5:
                train_comments.append(comment)
            elif alt_counter == 6:
                test_comments.append(comment)
            elif alt_counter == 7:
                val_comments.append(comment)
                alt_counter = 0

    with open(PATH_OUT_ARCELIK_ONLY_TRAIN, "wb") as file:
        pickle.dump(train_comments, file)
    with open(PATH_OUT_ARCELIK_ONLY_TEST, "wb") as file:
        pickle.dump(val_comments, file)
    with open(PATH_OUT_ARCELIK_ONLY_VAL, "wb") as file:
        pickle.dump(test_comments, file)


def generateArcelikPureUnseenTestSplit(all_comments):
    train_comments = []
    val_comments = []
    test_comments = []

    recipes_per_sub = {}
    subs_per_recipe = {}

    for comment in all_comments:
        sub = comment["subs"]
        recipe_id = comment["id"]
        if sub not in list(recipes_per_sub.keys()):
            recipes_per_sub[sub] = []
        recipes_per_sub[sub].append(comment)
        if recipe_id not in list(subs_per_recipe.keys()):
            subs_per_recipe[recipe_id] = []
        subs_per_recipe[recipe_id].append(comment)

    recipes_per_sub = dict(sorted(recipes_per_sub.items(), key=lambda item: len(item[1])))
    subs_per_recipe = dict(sorted(subs_per_recipe.items(), key=lambda item: len(item[1])))

    few_recipes_threshold = 3
    subs_with_few_recipes = {sub: recs for sub, recs in list(recipes_per_sub.items()) if len(recs) <= 3}
    subs_with_many_recipes = {sub: recs for sub, recs in list(recipes_per_sub.items()) if len(recs) >= 3}

    few_recipes = []
    for _sub, comments in subs_with_few_recipes.items():
        for comment in comments:
            if comment not in few_recipes:
                few_recipes.append(comment)
    few_recipes_sorted = sorted(few_recipes, key=lambda item: len(subs_per_recipe[item["id"]]))

    many_recipes = []
    for _sub, comments in subs_with_many_recipes.items():
        for comment in comments:
            if comment not in few_recipes_sorted and comment not in many_recipes:
                many_recipes.append(comment)


    # just checking if the order is right
    # for recipe in few_recipes_sorted:
    #     print(len(subs_per_recipe[recipe["id"]]))

    for comment in few_recipes_sorted:
        if len(test_comments) < 120:
            test_comments.append(comment)
        elif len(val_comments) < 60:
            val_comments.append(comment)
        else:
            train_comments.append(comment)

    for comment in many_recipes:
        if len(test_comments) < 120:
            test_comments.append(comment)
        elif len(val_comments) < 60:
            val_comments.append(comment)
        else:
            train_comments.append(comment)

    with open(PATH_OUT_ARCELIK_UNSEEN_TRAIN, "wb") as file:
        pickle.dump(train_comments, file)
    with open(PATH_OUT_ARCELIK_UNSEEN_TEST, "wb") as file:
        pickle.dump(test_comments, file)
    with open(PATH_OUT_ARCELIK_UNSEEN_VAL, "wb") as file:
        pickle.dump(val_comments, file)

def generateArcelikFiveFoldSplits(all_comments):
    """Generates 5 fold xval splits (generated val test sets are identical)

    Args:
        all_comments (_type_): Total number of samples
    """
    # shuffle comments
    shuffled_comments = random.sample(all_comments, len(all_comments))
    random.shuffle(shuffled_comments)
    random.shuffle(shuffled_comments)

    # split into 5 groups
    counter = 0
    groups = [[],[],[],[],[]]

    for comment in shuffled_comments:
        groups[counter % 5].append(comment)
        counter += 1


    Path(PATH_OUT_ARCELIK_FIFE_FOLD_DIR).mkdir(parents=True, exist_ok=True)

    # create splits from the groups and save them to file
    for i in range(len(groups)):
        train_path = os.path.join(PATH_OUT_ARCELIK_FIFE_FOLD_DIR, f"train_comments_subs_{i}.pkl")
        test_path = os.path.join(PATH_OUT_ARCELIK_FIFE_FOLD_DIR, f"test_comments_subs_{i}.pkl")
        val_path = os.path.join(PATH_OUT_ARCELIK_FIFE_FOLD_DIR, f"val_comments_subs_{i}.pkl")

        test_group = groups[i]
        train_group = []

        for k in range(len(groups)):
            if k != i:
                train_group += groups[k]

        # store splits
        with open(train_path, "wb") as file:
            pickle.dump(train_group, file)
        with open(test_path, "wb") as file:
            pickle.dump(test_group, file)
        with open(val_path, "wb") as file:
            pickle.dump(test_group, file)
    return



def generateArcelicGISMOSplits():
    # remove the recipes for arcelik evaluation from the train and val sets
    pass

def getPositiveSamples(samples):
    positive_samples = [sample for sample in samples if sample['consensual_answers']['fit'] == 1]
    test = [sample for sample in samples if sample['consensual_answers']['fit'] == 1 and sample['consensual_answers']['tastechange'] == 0]

    good_but_change_instructions = [sample for sample in samples if sample['consensual_answers']['fit'] == 1 and sample['consensual_answers']['processchange'] == 0]
    return positive_samples

def getNegativeSamples(samples):
    negative_samples = [sample for sample in samples if sample['consensual_answers']['fit'] == 0]
    return negative_samples


def getAdditionalPositiveGPTSuggestions(already_positive_samples, samples, nodes):
    potential_additional_samples = [sample for sample in samples if sample['consensual_answers']['selection'] is not None]

    node_labels = [node[1] for node in nodes]

    selected_positive_samples = []
    for sample in potential_additional_samples:
        # check potential samples, if they can be matched to flavorgraph nodes
        source_raw = sample['main_ingredient']
        target_raw = sample['consensual_answers']['selection']

        source = None
        target = None

        closest_source_match = process.extractOne(source_raw, node_labels)
        if closest_source_match and closest_source_match[1] > MATCH_THRESHOLD:
            source = closest_source_match[0]

        closest_target_match = process.extractOne(target_raw, node_labels)
        if closest_target_match and closest_target_match[1] > MATCH_THRESHOLD:
            target = closest_target_match[0]

        #remove same - same (after mapping) susbtitutions
        if (source == target):
            continue

        if source and target:
            new_sub_tuple = (source, target)
            # check potential samples, if they are already in the positive samples
            if (source != sample['sample_sub'][0]) or (target != sample['sample_sub'][1]):
                # if both are the case, add them to selected additional samples
                new_sample = {
                    'id': sample['id'],
                    'ingredients': sample['ingredients'],
                    'subs': new_sub_tuple
                }
                selected_positive_samples.append(new_sample)
    return selected_positive_samples

def clean_survey_samples_and_add_additional(positive_samples, additional_samples):
    # clean and bring to input comment format
    final_total_comments = []
    for pos_sample in positive_samples:
        new_tuple = (pos_sample["sample_sub"][0], pos_sample["sample_sub"][1])
        new_sample = {
            'id': pos_sample['id'],
            'ingredients': pos_sample['ingredients'],
            'subs': new_tuple
        }
        final_total_comments.append(new_sample)

    # add the additional samples
    for additional_sample in additional_samples:
        final_total_comments.append(additional_sample)

    return final_total_comments

def inspect_arc_only_samples(total_arcelik_only_samples):
    # check distinct targets for source.
    source_target_counter = {}

    tuples_for_rec_cnt = {0: 0, 1:0, 2:0, 3:0, 4: 0, 5:0, 6:0, 7:0, 8: 0, 9:0, 10:0, 111:0}
    distinct_targets_for_source = {}

    distinct_recipes_ids = []
    distinct_sub_tuples = []

    for comment in total_arcelik_only_samples:
        recipe_id = comment["id"]
        source = comment["subs"][0]
        target = comment["subs"][1]

        if recipe_id not in distinct_recipes_ids:
            distinct_recipes_ids.append(recipe_id)

        sub_tuple = (source, target)
        if sub_tuple not in distinct_sub_tuples:
            distinct_sub_tuples.append(sub_tuple)

        if source not in list(source_target_counter.keys()):
            source_target_counter[source] = {}
        if target not in list(source_target_counter[source].keys()):
            source_target_counter[source][target] = 0
        source_target_counter[source][target] += 1

    for source, _target in source_target_counter.items():
        for target, val in _target.items():
            if val in list(tuples_for_rec_cnt.keys()):
                tuples_for_rec_cnt[val] += 1
            else:
                tuples_for_rec_cnt[111] += 1
            print(f"subs [{source}->{target}]: {val}")

        n_distinct_targets = len(list(_target.keys()))
        if n_distinct_targets not in distinct_targets_for_source:
            distinct_targets_for_source[n_distinct_targets] = 0
        distinct_targets_for_source[n_distinct_targets] += 1
    print(f"recipes per sub tuples. {tuples_for_rec_cnt}")
    print(f"count of sources with x distinct targets: {distinct_targets_for_source}")
    print(f"Number of distinct recipes: {len(distinct_recipes_ids)}")
    print(f"Number of distinct substitution tuples: {len(distinct_sub_tuples)}")


def inspect_arc_only_splits():
    with open(PATH_OUT_ARCELIK_ONLY_TRAIN, "rb") as file:
        train_comments = pickle.load(file)
    with open(PATH_OUT_ARCELIK_ONLY_TEST, "rb") as file:
        val_comments = pickle.load(file)
    with open(PATH_OUT_ARCELIK_ONLY_VAL, "rb") as file:
        test_comments = pickle.load(file)

def main():
    DO_CREATE_PURE_SPLIST = False
    DO_CREATE_PURE_COLD_SPLITS = False
    DO_CREATE_FIVE_FOLD_SPLIST = False

    TMP_TOTAL_ARCELIK_ONLY_COMMENTS_PATH = "./outputs/new_comments/tmp_total_arcelik_only_comments.pkl"

    if os.path.exists(TMP_TOTAL_ARCELIK_ONLY_COMMENTS_PATH):
        with open(TMP_TOTAL_ARCELIK_ONLY_COMMENTS_PATH, 'rb') as file:
            total_arcelik_only_samples = pickle.load(file)
    else:
        # should we want all tuples in all splits, or should we also test ood prediction? (might be too few samples)
        survey_samples_with_answers = loadSurveySamplesWithAnswers()
        negative_samples = getNegativeSamples(survey_samples_with_answers)
        postive_samples = getPositiveSamples(survey_samples_with_answers)


        flavorgraphNodes = loadFlavourgraphIngrNodes(NODES_PATH)
        additional_positive_samples = getAdditionalPositiveGPTSuggestions(postive_samples, survey_samples_with_answers, flavorgraphNodes)

        total_arcelik_only_samples = clean_survey_samples_and_add_additional(postive_samples, additional_positive_samples)

        with open(TMP_TOTAL_ARCELIK_ONLY_COMMENTS_PATH, "wb") as file:
            pickle.dump(total_arcelik_only_samples, file)

    # * are negative samples from the original sample sets?
    gismo_train, gismo_val, gismo_test = loadGismoSplits()
    survey_samples_with_answers = loadSurveySamplesWithAnswers()
    negative_samples = getNegativeSamples(survey_samples_with_answers)
    negative_samples_from_r1msubs = [] # there are 9 of them
    negative_samples_not_from_r1msubs = [] # and 20 of those
    for negative_sample in negative_samples:
        sample_sub = (negative_sample["sample_sub"][0], negative_sample["sample_sub"][1])
        sample_recipe_id = negative_sample["id"]
        already_found = False
        for train_sample in gismo_train:
            if train_sample["subs"] == sample_sub and train_sample["id"] == sample_recipe_id:
                negative_samples_from_r1msubs.append(negative_sample)
                already_found = True
                break
        for val_sample in gismo_val:
            if val_sample["subs"] == sample_sub and val_sample["id"] == sample_recipe_id:
                negative_samples_from_r1msubs.append(negative_sample)
                already_found = True
                break
        for test_sample in gismo_test:
            if test_sample["subs"] == sample_sub and test_sample["id"] == sample_recipe_id:
                negative_samples_from_r1msubs.append(negative_sample)
                already_found = True
                break
        if not already_found:
            negative_samples_not_from_r1msubs.append(negative_sample)


    # arcelik_only_recipe_ids = list(set([sample["id"] for sample in total_arcelik_only_samples]))

    # gismo_train, gismo_val, gismo_test = loadGismoSplits()

    inspect_arc_only_samples(total_arcelik_only_samples)

    if DO_CREATE_PURE_SPLIST:
        generateArcelikPureSplits(total_arcelik_only_samples)


    if DO_CREATE_PURE_COLD_SPLITS:
        generateArcelikPureUnseenTestSplit(total_arcelik_only_samples)


    if DO_CREATE_FIVE_FOLD_SPLIST:
        generateArcelikFiveFoldSplits(total_arcelik_only_samples)

    # get the original gismo/recipe1M samples and splits
    # generateArcelicGISMOSplits()

    return

if __name__ == "__main__":
    main()