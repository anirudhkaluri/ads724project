#autoscale only pods
import subprocess
import sys
import time
import math
from datetime import datetime
import pandas as pd
# === CONFIG ===
CLUSTER_NAME = "ads-project-eks-cluster"
NODEGROUP_NAME = "ads-project-nodegroup-5"
DEPLOYMENT_NAME_APP = "vectorexp-deployment"
DEPLOYMENT_NAME_LLM = "ollama-deployment"
NAMESPACE = "default"
PODS_PER_NODE = 1
WAIT_TIMEOUT = 600   # Max wait time in seconds (10 minutes)
POLL_INTERVAL = 10   # How often to check pod status
# ==============

def scale_nodegroup(desired_nodes):
    min_nodes = max(1, desired_nodes - 1)
    max_nodes = desired_nodes + 1

    print(f"Scaling nodegroup to {desired_nodes} nodes...")
    cmd = [
        "eksctl", "scale", "nodegroup",
        "--cluster", CLUSTER_NAME,
        "--name", NODEGROUP_NAME,
        "--nodes", str(desired_nodes),
        "--nodes-min", str(min_nodes),
        "--nodes-max", str(max_nodes),
        "--wait"
    ]
    subprocess.run(cmd, check=True)
    print("✅ Nodegroup scaled to", desired_nodes)

def wait_for_nodes_ready(expected_count):
    print(f"⏳ Waiting for {expected_count} Ready nodes...")
    start_time = time.time()

    while time.time() - start_time < WAIT_TIMEOUT:
        cmd = ["kubectl", "get", "nodes", "--no-headers"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().splitlines()
        ready_nodes = [line for line in lines if " Ready " in line]
        ready_count = len(ready_nodes)

        print(f"✅ {ready_count}/{expected_count} nodes ready", end="\r")
        # if ready_count >= expected_count:
        #     print(f"\n✅ All {ready_count} nodes are Ready.")
        #     return
        if ready_count == expected_count:
            print(f"\n✅ All {ready_count} nodes are Ready.")
            return

        time.sleep(POLL_INTERVAL)

    print(f"\n❌ Timeout: Only {ready_count} nodes became Ready.")
    sys.exit(1)

def get_total_node_count():
    cmd = ["kubectl", "get", "nodes", "--no-headers"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error fetching nodes:", result.stderr)
        return 0

    # Count the number of lines in the output (one per node)
    node_count = len(result.stdout.strip().splitlines())
    return node_count

def scale_deployment(replicas):
    for deployment_name in [DEPLOYMENT_NAME_APP, DEPLOYMENT_NAME_LLM]:
        print(f"Scaling deployment '{deployment_name}' to {replicas} pods...")
        cmd = [
            "kubectl", "scale",
            f"deployment/{deployment_name}",
            "--replicas", str(int(replicas)),
            "-n", NAMESPACE
        ]
        subprocess.run(cmd, check=True)
        print(f"✅ Deployment '{deployment_name}' scaled to {replicas} pods")

def wait_for_pods_ready(deployment_name, expected_replicas):
    print(f"⏳ Waiting for all pods in '{deployment_name}' to be Running...")
    start_time = time.time()

    while time.time() - start_time < WAIT_TIMEOUT:
        cmd = [
            "kubectl", "get", "deployment", deployment_name,
            "-n", NAMESPACE,
            "-o", "jsonpath={.status.readyReplicas}"
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            ready = int(result.stdout.strip() or 0)

            print(f"✅ {ready}/{expected_replicas} pods ready", end="\r")
            """ if ready >= expected_replicas:
                print(f"\n✅ All {ready} pods for '{deployment_name}' are ready.")
                return """
            if ready == expected_replicas:
                print(f"\n✅ All {ready} pods for '{deployment_name}' are ready.")
                return 
        except Exception:
            pass

        time.sleep(POLL_INTERVAL)

    print(f"\n❌ Timeout: Not all pods for '{deployment_name}' became ready in time.")
    sys.exit(1)

# if __name__ == "__main__":
#     if len(sys.argv) != 2:
#         print("Usage: python scale_cluster_custom.py <desired_node_count>")
#         sys.exit(1)
#desired_node_count = int(sys.argv[1])

def scaleNodes(reqNodeCount):
    try:
        desired_node_count=reqNodeCount
        total_nodes=get_total_node_count()
        if total_nodes<desired_node_count:
            print("UPSCALING FROM: ", total_nodes, " TO: ",desired_node_count)
            replicas = math.floor(desired_node_count * PODS_PER_NODE)
            time_x = datetime.now()
            scale_nodegroup(desired_node_count)
            wait_for_nodes_ready(desired_node_count)

            time_y = datetime.now()
            scale_deployment(replicas)
            wait_for_pods_ready(DEPLOYMENT_NAME_APP, replicas)
            wait_for_pods_ready(DEPLOYMENT_NAME_LLM, replicas)

            time_z = datetime.now()
            time_y_minus_x = (time_y - time_x).total_seconds()
            time_z_minus_y = (time_z - time_y).total_seconds()
            time_z_minus_x = (time_z - time_x).total_seconds()
            #up.append({'upscaling_nodes':time_y_minus_x,'upscaling_pods':time_z_minus_y,'total_time':time_z_minus_x,'start':total_nodes,'end':desired_node_count})

            print(f"\nDuration (Y - X): {time_y_minus_x:.2f} seconds")
            print(f"Duration (Z - Y): {time_z_minus_y:.2f} seconds")
            print(f"Total Duration (Z - X): {time_z_minus_x:.2f} seconds")
        elif total_nodes>desired_node_count:
            print("DOWNSCALING FROM: ", total_nodes, " TO: ",desired_node_count)
            replicas = math.floor(desired_node_count * PODS_PER_NODE)
            time_x = datetime.now()
            scale_deployment(replicas)
            wait_for_pods_ready(DEPLOYMENT_NAME_APP, replicas)
            wait_for_pods_ready(DEPLOYMENT_NAME_LLM, replicas)

            time_y = datetime.now()
            scale_nodegroup(desired_node_count)
            wait_for_nodes_ready(desired_node_count)

            time_z = datetime.now()
            time_y_minus_x = (time_y - time_x).total_seconds()
            time_z_minus_y = (time_z - time_y).total_seconds()
            time_z_minus_x = (time_z - time_x).total_seconds()
           
            print(f"\nDuration (Y - X): {time_y_minus_x:.2f} seconds")
            print(f"Duration (Z - Y): {time_z_minus_y:.2f} seconds")
            print(f"Total Duration (Z - X): {time_z_minus_x:.2f} seconds")
        else:
            print("NO SCALING")    

        
        

    except subprocess.CalledProcessError as e:
        print("❌ Command failed:", e)
        sys.exit(1)
        

