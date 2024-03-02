# Statistical Ingredient Substitutions

This reposytory contains various preprocessing scripts, analysis scripts and utilities for ingredient substitutions, especially related to graph based ingredient susbtitutions and the generation of a new substitution dataset.

## General prerequisits

- you can set up the required packages by importing the conda environment from the [environment.yml](environment.yml)

## ArcSubs - singredient substitutions conditional on the recipe context

- Scripts and notebooks related to the creation and evaluation of a user survey are prefixed with

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


- `calc_recipe_ingredient_info_distances.py` is mostly used for preprocessing and providing the logic for the recommendation calculation
- `experiments_alt_ingredient_subs.ipynb` is used for exploring the recommendations for different recipes
- to make this work, only the following files are needed in the `inputs` directory:
  - `train_comments_susb.pkl` [download from gismo](https://dl.fbaipublicfiles.com/gismo/train_comments_subs.pkl)
  - `test_comments_susb.pkl` [download from gismo](https://dl.fbaipublicfiles.com/gismo/test_comments_subs.pkl)
  - `val_comments_susb.pkl` [download from gismo](https://dl.fbaipublicfiles.com/gismo/val_comments_subs.pkl) all those contain recipes incl. recipe id, ground truth substitution pair, ingredient list
  - `graph/nodes_191120.csv` [download form flavorgraph](https://github.com/lamypark/FlavorGraph/blob/master/input/nodes_191120.csv) contains the list of nodes in flavour graph and some additional features; relevant info can be obtained by the `get_graph_nodes` function
  - the train, test, and val sets are provided by facebook and their [gismo project](https://github.com/facebookresearch/gismo/tree/main/gismo), the graph nodes are provided by [flavorgraph](https://github.com/lamypark/FlavorGraph)

- recipe1m seems to [live on Kaggle](https://www.kaggle.com/datasets/kmader/layer-urls/) now

- however even though it might run with only the above described files, computation can take a long time. Using the following pre-processed files can help:
  - `./outputs/mutual_info_dict_with_self_info.pkl`