# Usage

- required packages that are not in the standard library are:
  - pandas
  - sklearn
  - numpy

- `calc_recipe_ingredient_info_distances.py` is mostly used for preprocessing and providing the logic for the recommendation calculation
- `experiments_alt_ingredient_subs.ipynb` is used for exploring the recommendations for different recipes
- to make this work, only the following files are needed in the `inputs` directory:
  - `train_comments_susb.pkl` [download from gismo](https://dl.fbaipublicfiles.com/gismo/train_comments_subs.pkl)
  - `test_comments_susb.pkl` [download from gismo](https://dl.fbaipublicfiles.com/gismo/test_comments_subs.pkl)
  - `val_comments_susb.pkl` [download from gismo](https://dl.fbaipublicfiles.com/gismo/val_comments_subs.pkl) all those contain recipes incl. recipe id, ground truth substitution pair, ingredient list
  - `graph/nodes_191120.csv` [download form flavorgraph](https://github.com/lamypark/FlavorGraph/blob/master/input/nodes_191120.csv) contains the list of nodes in flavour graph and some additional features; relevant info can be obtained by the `get_graph_nodes` function
  - the train, test, and val sets are provided by facebook and their [gismo project](https://github.com/facebookresearch/gismo/tree/main/gismo), the graph nodes are provided by [flavorgraph](https://github.com/lamypark/FlavorGraph)

- however even though it might run with only the above described files, computation can take a long time. Using the following pre-processed files can help:
  - `./outputs/mutual_info_dict_with_self_info.pkl`