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
            else:
                recipes_in_which_sub_ingrs_are_not_in_ingr_list.append(recipe_id)

    return recipes_per_substitution, recipes_in_which_sub_ingrs_are_not_in_ingr_list



##################

import nltk
from nltk.corpus import stopwords
from collections import Counter

nltk.download("punkt")
nltk.download("stopwords")

# Example recipe text
recipe_text = """
Baked Ziti
Ingredients
1 pound dry ziti pasta
1 onion, chopped
1 pound lean ground beef
2 (26 ounce) jars spaghetti sauce
6 ounces provolone cheese, sliced
1 ½ cups sour cream
6 ounces mozzarella cheese, shredded
2 tablespoons grated Parmesan cheese
"""

# Tokenize the recipe text
words = nltk.word_tokenize(recipe_text.lower())

# Remove stopwords (common words like "a", "an", "the", etc.)
stop_words = set(stopwords.words("english"))
filtered_words = [word for word in words if word.isalnum() and word not in stop_words]

# Count the frequency of each ingredient word
ingredient_counts = Counter(filtered_words)

# Find the most common ingredient (main ingredient)
main_ingredient, main_ingredient_count = ingredient_counts.most_common(1)[0]

print("Main Ingredient:", main_ingredient)
print("Frequency:", main_ingredient_count)

#########

import re

# Example recipe text


# Function to extract ingredients and quantities
def extract_ingredients_with_quantities(recipe_text):
    ingredients = []
    # Split the text into lines
    lines = recipe_text.split('\n')

    # Regular expression pattern to match quantities and ingredients
    pattern = r'(\d+(\s+\d+/\d+)?)\s+(\S.*)'

    for line in lines:
        # Check if the line matches the pattern
        match = re.match(pattern, line)
        if match:
            quantity = match.group(1)
            ingredient = match.group(3)
            ingredients.append((quantity, ingredient))

    return ingredients

# Extract ingredients with quantities
ingredient_list = extract_ingredients_with_quantities(recipe_text)

# Find the ingredient with the highest quantity
main_ingredient = max(ingredient_list, key=lambda x: x[0])

print("Main Ingredient:", main_ingredient[1])
print("Quantity:", main_ingredient[0])

#########

import re
from fractions import Fraction

# Example recipe text


# Function to normalize quantities and units
def normalize_quantity(quantity_str):
    quantity_str = quantity_str.strip()
    # Handle common unit variations
    unit_mapping = {
        "oz": "ounce",
        "ounces": "ounce",
        "lb": "pound",
        "pounds": "pound",
        "cup": "cup",
        "cups": "cup",
        "tbsp": "tablespoon",
        "tablespoons": "tablespoon",
        "tsp": "teaspoon",
        "teaspoons": "teaspoon",
    }
    for key, value in unit_mapping.items():
        quantity_str = quantity_str.replace(key, value)

    # Use regular expressions to extract quantities and fractions
    quantity_match = re.match(r"(\d+\s*(?:\d+/\d+)?)\s*(\S.*)", quantity_str)
    if quantity_match:
        quantity = quantity_match.group(1)
        ingredient = quantity_match.group(2)

        # Normalize fractions and convert to float
        fraction_parts = quantity.split()
        total_quantity = 0.0
        for part in fraction_parts:
            try:
                total_quantity += float(Fraction(part))
            except ValueError:
                pass  # Ignore non-fractional parts

        return total_quantity, ingredient.strip()

    return None, quantity_str

# Function to extract ingredients with normalized quantities
def extract_ingredients_with_normalized_quantities(recipe_text):
    ingredients = []
    # Split the text into lines
    lines = recipe_text.split('\n')

    for line in lines:
        # Extract quantity and ingredient
        quantity, ingredient = normalize_quantity(line)
        if quantity is not None:
            ingredients.append((quantity, ingredient))

    return ingredients

# Extract ingredients with normalized quantities
ingredient_list = extract_ingredients_with_normalized_quantities(recipe_text)

# Find the ingredient with the highest quantity
main_ingredient = max(ingredient_list, key=lambda x: x[0])

print("Main Ingredient:", main_ingredient[1])
print("Quantity:", main_ingredient[0])

#########

import re
from fractions import Fraction



# Function to convert quantities to grams
def convert_to_grams(quantity, unit):
    unit_to_grams = {
        "gram": 1,
        "ounce": 28.3495,
        "pound": 453.592,
        "cup": 236.588,
        "tablespoon": 14.7868,
        "teaspoon": 4.92892,
    }
    return quantity * unit_to_grams.get(unit, 1)

# Function to extract ingredients with quantities in grams
def extract_ingredients_with_normalized_quantities(recipe_text):
    ingredients = []
    # Split the text into lines
    lines = recipe_text.split('\n')

    for line in lines:
        # Extract quantity and ingredient
        quantity, unit, ingredient = normalize_quantity(line)
        if quantity is not None:
            quantity_in_grams = convert_to_grams(quantity, unit)
            ingredients.append((quantity_in_grams, ingredient))

    return ingredients

# Extract ingredients with quantities in grams
ingredient_list = extract_ingredients_with_normalized_quantities(recipe_text)

# Find the ingredient with the highest quantity
main_ingredient = max(ingredient_list, key=lambda x: x[0])

print("Main Ingredient:", main_ingredient[1])
print("Quantity (in grams):", main_ingredient[0])



