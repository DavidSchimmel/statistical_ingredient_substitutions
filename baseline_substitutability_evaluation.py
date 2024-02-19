import torch
import os
import pickle

substitutabilites = torch.load(os.path.abspath("./baseline_substitutability/cos_similarities.pt"))

ingr_name_2_subst_col_path = os.path.join("./baseline_substitutability/ingr_2_col.pkl")
sample_2_subst_row_path = os.path.join("./baseline_substitutability/sample_2_row.pkl")
with open(ingr_name_2_subst_col_path, "rb") as ingr_2_subst_col_file:
    ingr_name_2_subst_col = pickle.load(ingr_2_subst_col_file)
with open(sample_2_subst_row_path, "rb") as sample_2_subst_row_file:
    sample_2_subst_row = pickle.load(sample_2_subst_row_file)

test_samples_path = os.path.abspath("./inputs/test_comments_subs.pkl")
with open(test_samples_path, "rb") as test_samples_file:
    test_samples = pickle.load(test_samples_file)

TMP_TOTAL_ARCELIK_ONLY_COMMENTS_PATH = "./outputs/new_comments/tmp_total_arcelik_only_comments.pkl"
filter_for_arc = True
if filter_for_arc:
    with open(TMP_TOTAL_ARCELIK_ONLY_COMMENTS_PATH, 'rb') as file:
        total_arcelik_only_samples = pickle.load(file)
    train_samples_path = os.path.abspath("./inputs/test_comments_subs.pkl")
    with open(test_samples_path, "rb") as test_samples_file:
        test_samples = pickle.load(test_samples_file)
    val_samples_path = os.path.abspath("./inputs/test_comments_subs.pkl")
    with open(test_samples_path, "rb") as test_samples_file:
        test_samples = pickle.load(test_samples_file)
    test_samples = []

valid_sample_cnt = 0
r_rank_sum = 0
n_hit_at_1 = 0
n_hit_at_3 = 0
n_hit_at_10 = 0
distinct_recs_per_source = {}

skipped_samples = []
for recipe in test_samples:
    recipe_id = recipe["id"]
    source = recipe["subs"][0]
    gt_target = recipe["subs"][1]
    if source not in list(distinct_recs_per_source.keys()):
        distinct_recs_per_source[source] = []


    if gt_target not in list(ingr_name_2_subst_col.keys()):
        skipped_samples.append(recipe)
        continue
    gt_target_col = ingr_name_2_subst_col[gt_target]

    if recipe_id not in list(sample_2_subst_row.keys()):
        skipped_samples.append(recipe)
        continue

    if source not in list(sample_2_subst_row[recipe_id].keys()):
        skipped_samples.append(recipe)
        continue

    if gt_target not in list(sample_2_subst_row[recipe_id][source].keys()):
        skipped_samples.append(recipe)
        continue

    substitutabilities_row_idx = sample_2_subst_row[recipe_id][source][gt_target]
    substitutabilites_row = substitutabilites[substitutabilities_row_idx]

    top_recommendation_idx = torch.argmax(substitutabilites_row)
    distinct_recs_per_source[source].append(top_recommendation_idx)

    cols_with_substitutabilities = {idx: col for idx, col in enumerate(substitutabilites_row)}
    #sort that cols according to their score (similiarity should be high -> descending order)
    cols_with_substitutabilities = dict(sorted(cols_with_substitutabilities.items(), key=lambda item: item[1], reverse=True))
    gt_target_rank = list(cols_with_substitutabilities.keys()).index(gt_target_col) - 1

    valid_sample_cnt += 1

    if gt_target_rank == 0:
        r_rank_sum += 1
    else:
        r_rank_sum += 1 / gt_target_rank

    if gt_target_rank <= 0:
        n_hit_at_1 += 1
    if gt_target_rank <= 2:
        n_hit_at_3 += 1
    if gt_target_rank <= 9:
        n_hit_at_10 += 1

mrr = r_rank_sum / valid_sample_cnt * 100
hit_at_1 = n_hit_at_1 / valid_sample_cnt
hit_at_3 = n_hit_at_3 / valid_sample_cnt
hit_at_10 = n_hit_at_10 / valid_sample_cnt


print(f"skipped samples: {skipped_samples}")
print(f"mrr: {mrr}")
print(f"Hits@1: {hit_at_1}")
print(f"Hits@3: {hit_at_3}")
print(f"Hits@10: {hit_at_10}")




undiverse_top_rank_count = 0
undiverse_top_rank_count_with_more_than_10_recipes = 0
abs_div_sum = 0
distinct_source_count = 0
for source, recommendations in distinct_recs_per_source.items():
    distinct_targets = []
    for target in recommendations:
        if target not in distinct_targets:
            distinct_targets.append(target)

    n_unique_preds = len(distinct_targets)
    distinct_source_count += 1
    abs_div_sum += n_unique_preds
    if n_unique_preds <= 1:
        undiverse_top_rank_count += 1
        if len(recommendations) > 10:
            undiverse_top_rank_count_with_more_than_10_recipes += 1

print(f"average top rank diversity: {abs_div_sum / distinct_source_count}")
print(f"total number of distinct substitution sources: {abs_div_sum}")
print(f"number of substitution sources which have only 1 recommended ingredient: {undiverse_top_rank_count}")
print(f"number of substitution sources which have only 1 recommended ingreident and which is applied to more than 10 recipes: {undiverse_top_rank_count_with_more_than_10_recipes}")

print("done")