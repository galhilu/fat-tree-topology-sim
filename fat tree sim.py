from typing import List, Tuple
import random
import matplotlib.pyplot as plt
import numpy as np


class Link:
    def __init__(self, direction: str, other_end_id: int, failed: bool = False, capacity_gbps: float = 40.0):
        self.direction: str = direction     # upstream or downstream
        self.failed: bool = failed
        self.capacity_gbps: float = capacity_gbps
        self.other_end_id = other_end_id


class Switch:
    def __init__(self, switch_id: int, k: int, layer: str, pod_id: int | None = None):
        self.switch_id: int = switch_id
        self.k: int = k
        self.layer = layer            # leaf aggr or spine

        if self.layer == "leaf":
            pod_id = self.switch_id // (k // 2)               
            first_aggr_id = pod_id*(k//2)+((k**2)//2)
            self.links: List[Link] = [Link("upstream", i) for i in range(first_aggr_id, first_aggr_id+(k//2))]
            self.pod_id = pod_id

        elif self.layer == "aggr":
            pod_id = (self.switch_id-(k**2)//2) // (k // 2)
            first_leaf_id = pod_id*(k//2)
            self.links: List[Link] = [Link("downstream", i) for i in range(first_leaf_id, first_leaf_id+(k//2))]
            aggr_pos = (self.switch_id-((k**2)//2)) % (k//2)
            upstream_links = [Link("upstream", i) for i in range(k**2+((k//2)*aggr_pos), k**2+((k//2)*(aggr_pos+1)))]
            self.links.extend(upstream_links)                    
            self.pod_id = pod_id

        elif self.layer == "spine":
            spine_pos = self.switch_id -(k**2)
            first_aggr = (k**2)//2
            self.links: List[Link] = [Link("downstream", i) for i in range(first_aggr+spine_pos, k**2, k//2)]
            self.pod_id = -1

    def trip_links(self, fail_prob):
        failed_links = []
        for link in self.links:
            if (not link.failed) and (random.random() < fail_prob):   
                link.failed = True
                failed_links.append(link.other_end_id)
        return failed_links


class Topology:
    def __init__(self, k: int):
        self.k: int = k
        self.spine = [Switch(i, k, "spine") for i in range(k**2, k**2+(k//2)**2)]
        self.leaf: List[Switch] = []
        self.aggr: List[Switch] = []
        for pod_id in range(0, k):
            temp_leaf: List[Switch] = [Switch(pod_id*(k//2)+i, k, "leaf") for i in range(0, k//2)]      
            temp_aggr: List[Switch] = [Switch(pod_id*(k//2)+((k**2)//2)+i, k, "aggr") for i in range(0, k//2)]
            self.leaf.extend(temp_leaf) 
            self.aggr.extend(temp_aggr)
        self.switches: dict[int,Switch] = {s.switch_id: s for s in (self.leaf + self.aggr + self.spine)}

    def trip_links(self, fail_prob):
        for switch in self.aggr:
            failed_links = switch.trip_links(fail_prob)
            spines = [x for x in self.spine if x.switch_id in failed_links]
            leafs = [x for x in self.leaf if x.switch_id in failed_links]
            for s in spines + leafs:
                for l in s.links:
                    if l.other_end_id == switch.switch_id:
                        l.failed = True
                        break



def healthy_neighbors_of(topo: Topology, switch: Switch, direction: str) -> List[Switch]:

    neighbor_ids = [l.other_end_id for l in switch.links if (l.direction == direction and not l.failed)]
    return [topo.switches[x]  for x in neighbor_ids]

def count_paths_leaf_to_leaf(topo: Topology, src_leaf: Switch, dst_leaf: Switch) -> int:

    src_aggrs = healthy_neighbors_of(topo, src_leaf, "upstream")
    if not src_aggrs:
        return 0

    dst_aggrs = healthy_neighbors_of(topo, dst_leaf, "upstream")
    if not dst_aggrs:
        return 0
    
    if src_leaf.pod_id == dst_leaf.pod_id:
       src_aggrs_ids = [s.switch_id for s in  src_aggrs ]
       dst_aggrs_ids = [s.switch_id for s in  dst_aggrs ]
       return len([x for x in src_aggrs_ids if x in dst_aggrs_ids])
    
    else:
        src_spines: List[Switch] = []
        for s in src_aggrs:
            src_spines.extend(healthy_neighbors_of(topo, s, "upstream"))

        dst_spines: List[Switch] = []
        for s in dst_aggrs:
            dst_spines.extend(healthy_neighbors_of(topo, s, "upstream"))

        src_spines_ids = [s.switch_id for s in  src_spines ]
        dst_spines_ids = [s.switch_id for s in  dst_spines ]
        return len([x for x in src_spines_ids if x in dst_spines_ids])


def avg_paths_vs_p(k: int, probs: List[float], trials: int = 1):
    res_in_pod, res_out_pod = [],[]
    for p in probs:
        in_pod, out_pod = [],[]
        for _ in range(trials):
            topo = Topology(k)
            topo.trip_links(p)
            for src in range(0,k**2//2):
                for dst in range(src+1,k**2//2):
                    if src // (k // 2) == dst // (k // 2):
                        in_pod.append(count_paths_leaf_to_leaf(topo,topo.switches[src] , topo.switches[dst]))
                    else:
                        out_pod.append(count_paths_leaf_to_leaf(topo,topo.switches[src] , topo.switches[dst]))

        res_in_pod.append(sum(in_pod)/len(in_pod))
        res_out_pod.append(sum(out_pod)/len(out_pod))

    return res_in_pod,res_out_pod

def switches_with_multifails_at_1pct(k: int) -> int:
    topo = Topology(k)
    topo.trip_links(0.01)
    cnt = 0
    for sw in topo.leaf + topo.aggr + topo.spine:
        if sum(1 for l in sw.links if l.failed) >= 2:
            cnt += 1
    return cnt


def main():

    # 1) average number of paths as a function of link failure probability
    k_for_paths = 8  
    probs = [0.0, 0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6 ]

    avg_in ,avg_out = avg_paths_vs_p(k_for_paths, probs)

    plt.title("Number of paths by link fail prob")
    plt.plot(np.array(probs), np.array(avg_in))
    plt.plot(np.array(probs), np.array(avg_out))
    plt.legend(["in pod","out of pod"])
    plt.xlabel("Probability")
    plt.ylabel("Paths")
    plt.show()

    # 2) number of switches with multiple failed links (at a 1% failure rate) as a function of switch port count
    k = [4, 6, 8, 10, 12, 48]

    cnt = []
    for i in k:
        cnt.append(switches_with_multifails_at_1pct(i))

    plt.title("Switches with multiple failed links")
    plt.plot(np.array(k), np.array(cnt))
    plt.xlabel("Port count")
    plt.ylabel("Switches")
    plt.show()


    # 3) number of hosts supported by the network as a function of switch port count
    k = [4, 6, 8, 10, 12]
    
    cnt = []
    for i in k:
        cnt.append((i**3)//4)
    
    plt.title("Number of hosts supported vs switch port count")
    plt.plot(np.array(k), np.array(cnt))
    plt.xlabel("Port count")
    plt.ylabel("Hosts")
    plt.show()

if __name__ == "__main__":
    main()
