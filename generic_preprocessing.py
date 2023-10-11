import os


def getRecipesPerSubstitutionTuple(extended_recipes):
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
