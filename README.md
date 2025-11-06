 Fat-Tree Topology Sim – Quick README

This code runs three experiments on a k-ary fat-tree, to build intuition about path redundancy, failure impact, and scaling. for each experiment, there are tunable parameters as explained below, as well as a graph to visualize the results.


1) Average paths vs. link failure probability

Purpose: 
Show how the amount of paralle paths between leaf switches degrades as link failures increase. Graph shows seperatly amount of paths between leafs in the same pod and leafs that are not.

Changeable parameters:

  `k_for_paths`: int, switch port count, needs to be even.
  `probs`: list of floats, the list of failure probabilities to be tested.
  `trials`: int, number of repetitions for more accurate results.

--------------------------------

 2) Switches with multiple failed links @ 1% failure Rate

Purpose: 
For different `k`, count how many switches end up with more then 2 failed links when links fail with probability 1%.

Changeable parameters:

 `k_1p_fail`: list of ints, port counts to evaluate.

--------------------------------

3) Supported hosts vs. port count `k`

Purpose: 
Visualize theoretical host capacity scaling of a k-ary fat-tree.

Changeable parameters:

 `k_hosts`: list of ints, port counts to plot.

--------------------------------

Output:

Running the script displays three Matplotlib figures in sequence—one per experiment, reflecting the parameter values you choose above.
