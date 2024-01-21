import csv
import os
import pickle

from fuzzywuzzy import process

PATH_SURVEY_SAMPLES_WITH_ANSWERS = os.path.abspath("./survey_results_processed/survey_samples_with_answers.pkl")
PATH_IN_GISMO_TRAIN = os.path.abspath("./inputs/train_comments_subs.pkl")
PATH_IN_GISMO_TEST = os.path.abspath("./inputs/test_comments_subs.pkl")
PATH_IN_GISMO_VAL = os.path.abspath("./inputs/val_comments_subs.pkl")
PATH_OUT_ARCELIK_ONLY_TRAIN = os.path.abspath("./outputs/new_comments/arcelik_only/train_comments_subs.pkl")
PATH_OUT_ARCELIK_ONLY_TEST = os.path.abspath("./outputs/new_comments/arcelik_only/test_comments_subs.pkl")
PATH_OUT_ARCELIK_ONLY_VAL = os.path.abspath("./outputs/new_comments/arcelik_only/val_comments_subs.pkl")
PATH_OUT_ARCELIK_FILTERED_TRAIN = os.path.abspath("./outputs/new_comments/falvorgraph_appended/train_comments_subs.pkl")
PATH_OUT_ARCELIK_FILTERED_TEST = os.path.abspath("./outputs/new_comments/falvorgraph_appended/test_comments_subs.pkl")
PATH_OUT_ARCELIK_FILTERED_VAL = os.path.abspath("./outputs/new_comments/falvorgraph_appended/val_comments_subs.pkl")
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


def generateArcelicGISMOSplits():
    # remove the recipes for arcelik evaluation from the train and val sets
    pass

def getPositiveSamples(samples):
    positive_samples = [sample for sample in samples if sample['consensual_answers']['fit'] == 1]
    test = [sample for sample in samples if sample['consensual_answers']['fit'] == 1 and sample['consensual_answers']['tastechange'] == 0]
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

def main():
    DO_CREATE_PURE_SPLIST = False

    TMP_TOTAL_ARCELIK_ONLY_COMMENTS_PATH = "./outputs/new_comments/tmp_total_arcelik_only_comments.pkl"

    if os.path.exists(TMP_TOTAL_ARCELIK_ONLY_COMMENTS_PATH):
        with open(TMP_TOTAL_ARCELIK_ONLY_COMMENTS_PATH, 'rb') as file:
            total_arcelik_only_samples = pickle.load(file)
    else:
        # should we want all tuples in all splits, or should we also test ood prediction? (might be too few samples)
        survey_samples_with_answers = loadSurveySamplesWithAnswers()
        postive_samples = getPositiveSamples(survey_samples_with_answers)


        flavorgraphNodes = loadFlavourgraphIngrNodes(NODES_PATH)
        additional_positive_samples = getAdditionalPositiveGPTSuggestions(postive_samples, survey_samples_with_answers, flavorgraphNodes)

        total_arcelik_only_samples = clean_survey_samples_and_add_additional(postive_samples, additional_positive_samples)

        with open(TMP_TOTAL_ARCELIK_ONLY_COMMENTS_PATH, "wb") as file:
            pickle.dump(total_arcelik_only_samples, file)

    gismo_train, gismo_val, gismo_test = loadGismoSplits()

    if DO_CREATE_PURE_SPLIST:
        generateArcelikPureSplits(total_arcelik_only_samples)

    # get the original gismo/recipe1M samples and splits
    generateArcelicGISMOSplits()

    pass

if __name__ == "__main__":
    main()