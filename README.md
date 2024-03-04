# Statistical Ingredient Substitutions

This reposytory contains various preprocessing scripts, analysis scripts and utilities for ingredient substitutions, especially related to graph based ingredient susbtitutions and the generation of a new substitution dataset.

## General prerequisits

- you can set up the required packages by importing the conda environment from the [environment.yml](environment.yml)

## ArcSubs - singredient substitutions conditional on the recipe context

- Scripts and notebooks related to the creation and evaluation of a user survey are prefixed with

### General preprocessing

- Run the following 2 files in sequence to generate an extended recipes list from Recipe1M recipes:
  - `recipe1m\getting_layer_1.py`
  - `recipe1m\add_quantities_to_extended_recipes.py`
- The resulting list can contains recipes with title, ingredients sets, instruction lists and quantities per ingredient
- This can be used as input:
  - as input for [graph generation](https://github.com/DavidSchimmel/structured_recipe1m)
  - the list including the quantities is required for survey preprocessing
- This requires as input:
  - recipe1m `layer1.json` containing the recipe1M recipes, which is required to get, for example, the instructions
    - put the file into `./recipe1m/input/layer1.json`
  - GISMo samples:
    - `train_comments_susb.pkl` [download from gismo](https://dl.fbaipublicfiles.com/gismo/train_comments_subs.pkl)
    - `test_comments_susb.pkl` [download from gismo](https://dl.fbaipublicfiles.com/gismo/test_comments_subs.pkl)
    - `val_comments_susb.pkl` [download from gismo](https://dl.fbaipublicfiles.com/gismo/val_comments_subs.pkl)
    - put them into (`./inpust`)

### Preprocessing for survey

- related files:
  - `survey_parse_arcelik_recipes.py` -> parses an undisclosed dataset and matches the ingredients to [flavorgraph](https://github.com/lamypark/FlavorGraph) ingredient nodes.
  - `survey_pprint_recipes.ipynb` -> to inspect some of the samples chosen for the survey
  - `generic_preprocessing.py` -> preprocessing functions, mainly to estimate the normalized quantities of ingredients in recipes
  - `survey_preparation.ipynb` -> initial filtering of Recipe1MSubs samples based on various criteria
  - `survey_preparation_restricted_ingredients.ipynb` -> filter and generate survey samples from previously pre-filtered Recipe1MRecipes and a mapping of ingredients to Recipe1M/Flavorgraph ingredients (to condition the filtering on the number of mapped ingredients, whcih can be used to find recipes that use more familiar ingredienst)

### Generating Qualtrics survey files

- related files:
  - `survey_create_qualtrics_input_file.py`
  - while this approach is specific for the files that are used to generate the survey questions, the general approach of creating a text template including raw html can serve as a template for for other surveys if you want to import questions to Qualtrics

### Assessing survey results

- related files:
  - `survey_overview.ipynb`
  - `survey_results_stats.ipynb` -> statistical evalaution of survey responses
  - `survey_results_utils.py` -> some processing functions for the survey results and aggregating the answer chunks and different annotator responses

### Generating substitution ground truth samples

- related files:
  - `survey_results_splits.py` -> generate various data splits for training ML models

## Preliminary Substitutability based on 2nd order ingredient mutual information

- related files:
  - `calc_recipe_ingredient_info_distances.py`
    - calculates some matrices for mutual information between ingredients in the recipe dataset
    - needs the following files in the `./inputs/`
    - `train_comments_susb.pkl` [download from gismo](https://dl.fbaipublicfiles.com/gismo/train_comments_subs.pkl)
    - `test_comments_susb.pkl` [download from gismo](https://dl.fbaipublicfiles.com/gismo/test_comments_subs.pkl)
    - `val_comments_susb.pkl` [download from gismo](https://dl.fbaipublicfiles.com/gismo/val_comments_subs.pkl) all those contain recipes incl. recipe id, ground truth substitution pair, ingredient list
    - `graph/nodes_191120.csv` [download form flavorgraph](https://github.com/lamypark/FlavorGraph/blob/master/input/nodes_191120.csv) contains the list of nodes in flavour graph and some additional features; relevant info can be obtained by the `get_graph_nodes` function
  - `precalc_all_extended_recipe_2nd_order_cor_recs.py`
    - this produces the files that are required to train GISMo with the provided negative sampling strategies

  - for both files, check the constants in the `main()` function to see path and control flow

## Workflow for experiments

### Negative sampling

- load the prerequisits and run the scripts `recipe1m\getting_layer_1.py` and then `recipe1m\add_quantities_to_extended_recipes.py`
- import the prerequisites for `calc_recipe_ingredient_info_distances`, run the script until you have the `./outputs/mutual_info_dict_with_self_info.pkl`
- import the other prerequisites for `precalc_all_extended_recipe_2nd_order_cor_recs` and run that file (use the `train_comments_susb` (and test and val comments) for GISMo or for the Arcsubs, depending on which model you want to train)
- copy the resulting files `./outputs/precalced_substitutabilities/cos_similarities.pt`, `./outputs/precalced_substitutabilities/sample_2_row.pkl`, `./outputs/precalced_substitutabilities/ingr_2_col.pkl`  into GISMo into a directory `gismo\checkpoints\precalculated_substitutabilities` in the GISMo repository on the branch [um_mt_extensions](https://github.com/DavidSchimmel/gismo/tree/um_mt_extensions)

### Graph generation

- load the prerequisits and run the scripts `recipe1m\getting_layer_1.py` and then `recipe1m\add_quantities_to_extended_recipes.py`
- copy the generated `./recipe1m/output/extended_recipes_with_quantities.json` file into the `data\input` path in the [graph generation library](https://github.com/DavidSchimmel/structured_recipe1m), load the libraries other inputs and run the files
- from there, copy the desired nodes and edges files that can be found in that module's `data\output` directories into the [GISMo repo](https://github.com/DavidSchimmel/gismo/tree/um_mt_extensions) to the directory `gismo\checkpoints\graph`, change the names to `edges_191120.csv` and `nodes_191120.csv`
- then follow the instructions in the GISMo repo and run the experiments