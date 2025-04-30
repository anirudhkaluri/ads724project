from locust import HttpUser, task, between, LoadTestShape, events
import random
import time
import requests


import threading



import csv
import math
from itertools import zip_longest
import bisect
import pandas as pd

collected_memory = []
collected_cpu = []
time_array=[]
experiment_array=[]
stop_event = threading.Event()
PROM_URL = "http://127.0.0.1:9090/api/v1/query"
MEMORY_QUERY = """
(
  (node_memory_MemTotal_bytes - node_memory_MemFree_bytes - node_memory_Cached_bytes - node_memory_Buffers_bytes)
  / node_memory_MemTotal_bytes
) * 100
"""

CPU_QUERY = """
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[40s])) * 100)
"""



current_stage = 1



# Queries
queries = [
    "What degree did Sagar pursue at NC State University?",
    "Where did Anirudh complete his PhD?",
    "What field is Anirudh’s master’s degree in?",
    "Is Sagar also a PhD holder in Computer Science?",
    "When did Sagar start his Master’s degree?",
    "Has Anirudh been involved in Computer Science for over 10 years?",
    "Which university awarded Anirudh his Master’s degree?",
    "What academic path did Sagar follow after his MS?",
    "Who among the two studied at UC Berkeley for their PhD?",
    "Which institution did Sagar attend for his graduate studies?"
]


def cpu_memory_monitor(stop_event, interval=10, collected_cpu=[], collected_memory=[]):
    while not stop_event.is_set():
        try:
            mem_resp = requests.get(PROM_URL, params={'query': MEMORY_QUERY})
            cpu_resp = requests.get(PROM_URL, params={'query': CPU_QUERY})
            mem_resp.raise_for_status()
            cpu_resp.raise_for_status()
            mem_data = mem_resp.json()
            cpu_data = cpu_resp.json()
            #print(f"\n\n\n\n\nThe Query cpu_data is\n {cpu_data}")
        

            if mem_data["status"] == "success" and cpu_data["status"] == "success":
                mem_results = mem_data["data"]["result"]
                cpu_results = cpu_data["data"]["result"]
                #print(f"The cpu_data[data] is\n {cpu_data['data']}\n\n\n\n\n\n\n The cpu_data[data][results] is \n{cpu_data['data']['result']}")
                mem_sum=get_sum(mem_results)
                cpu_sum=get_sum(cpu_results)
                collected_memory.append(mem_sum)
                collected_cpu.append(cpu_sum)
                print(f"[Monitor] CPU Usage: {cpu_sum:.2f} | Memory Usage: {mem_sum:.2f}")
                temporary_array=[]
                temporary_array.append({'Time':time.time(),'CPU':cpu_sum,'MEMORY':mem_sum})
                temporary_data_frame = pd.DataFrame(temporary_array)
                temporary_data_frame.to_csv("cpu_usage_data.csv", mode='a', header=not pd.io.common.file_exists("cpu_usage_data.csv"), index=False)


            else:
                print("[Monitor] Error fetching data:") #, data.get("error", "Unknown error")

        except Exception as e:
            print(f"[Monitor] Error: Handle Exception")
            collected_memory.append(float('nan'))
            collected_cpu.append(float('nan'))
            time_array.append(time.time())


        time.sleep(interval)

monitor_thread = threading.Thread(target=cpu_memory_monitor, args=(stop_event, 10, collected_cpu,collected_memory))


class RAGUser(HttpUser):
    host = "http://ac4095edb3b45497185fbdaefe0f85a0-1384676893.us-east-1.elb.amazonaws.com"
    # wait_time = between(10, 20)

    @task(5)
    def regular_query(self):
        query = random.choice(queries)
        data = {"input": query}
        headers = {"Content-Type": "application/json"}
        start_time = time.time()

        with self.client.get(
            "/vector/ask",
            headers=headers,
            json=data,
            catch_response=True,
            timeout=30
        ) as response:
            duration = time.time() - start_time
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

# Custom load shape: updates every 60 seconds for 10 minutes
class StepLoadShape(LoadTestShape):
    """
    A step load shape that changes user count every minute over 10 minutes.
    """

    stages = [
        # {"duration": 10, "users": 2, "spawn_rate": 1},
        # {"duration": 20, "users": 2, "spawn_rate": 1},
        # {"duration": 30, "users": 2, "spawn_rate": 1},
    # --- Training (0 to 41) ---
    {"duration": 180 * 1, "users": 2, "spawn_rate": 1},   # 🟢
    {"duration": 180 * 2, "users": 4, "spawn_rate": 1},   # 🔺
    {"duration": 180 * 3, "users": 8, "spawn_rate": 2},   # 🔺
    {"duration": 180 * 4, "users": 12, "spawn_rate": 2},  # 🔴
    {"duration": 180 * 5, "users": 0, "spawn_rate": 1},   # 🔻
    {"duration": 180 * 6, "users": 3, "spawn_rate": 1},   # 🟢
    {"duration": 180 * 7, "users": 6, "spawn_rate": 1},   # 🔺
    {"duration": 180 * 8, "users": 10, "spawn_rate": 2},  # 🔴
    {"duration": 180 * 9, "users": 0, "spawn_rate": 1},   # 🔻

    {"duration": 180 * 10, "users": 2, "spawn_rate": 1},  # 🟢
    {"duration": 180 * 11, "users": 4, "spawn_rate": 1},  # 🔺
    {"duration": 180 * 12, "users": 10, "spawn_rate": 2}, # 🔴
    {"duration": 180 * 13, "users": 0, "spawn_rate": 1},  # 🔻

    {"duration": 180 * 14, "users": 3, "spawn_rate": 1},  # 🟢
    {"duration": 180 * 15, "users": 6, "spawn_rate": 1},  # 🔺
    {"duration": 180 * 16, "users": 12, "spawn_rate": 2}, # 🔴
    {"duration": 180 * 17, "users": 0, "spawn_rate": 1},  # 🔻

    {"duration": 180 * 18, "users": 2, "spawn_rate": 1},  # 🟢
    {"duration": 180 * 19, "users": 5, "spawn_rate": 1},  # 🔺
    {"duration": 180 * 20, "users": 10, "spawn_rate": 2}, # 🔴
    {"duration": 180 * 21, "users": 0, "spawn_rate": 1},  # 🔻

    {"duration": 180 * 22, "users": 3, "spawn_rate": 1},  # 🟢
    {"duration": 180 * 23, "users": 7, "spawn_rate": 2},  # 🔺
    {"duration": 180 * 24, "users": 13, "spawn_rate": 3}, # 🔴
    {"duration": 180 * 25, "users": 0, "spawn_rate": 1},  # 🔻

    {"duration": 180 * 26, "users": 2, "spawn_rate": 1},
    {"duration": 180 * 27, "users": 4, "spawn_rate": 1},
    {"duration": 180 * 28, "users": 8, "spawn_rate": 2},
    {"duration": 180 * 29, "users": 0, "spawn_rate": 1},

    {"duration": 180 * 30, "users": 3, "spawn_rate": 1},
    {"duration": 180 * 31, "users": 6, "spawn_rate": 1},
    {"duration": 180 * 32, "users": 11, "spawn_rate": 2},
    {"duration": 180 * 33, "users": 0, "spawn_rate": 1},

    {"duration": 180 * 34, "users": 2, "spawn_rate": 1},
    {"duration": 180 * 35, "users": 5, "spawn_rate": 1},
    {"duration": 180 * 36, "users": 10, "spawn_rate": 2},
    {"duration": 180 * 37, "users": 0, "spawn_rate": 1},

    {"duration": 180 * 38, "users": 3, "spawn_rate": 1},
    {"duration": 180 * 39, "users": 7, "spawn_rate": 2},
    {"duration": 180 * 40, "users": 12, "spawn_rate": 3},
    {"duration": 180 * 41, "users": 0, "spawn_rate": 1},

    # --- Testing (42 to 59) - repeat similar patterns ---
    {"duration": 180 * 42, "users": 3, "spawn_rate": 1},
    {"duration": 180 * 43, "users": 6, "spawn_rate": 1},
    {"duration": 180 * 44, "users": 12, "spawn_rate": 2},
    {"duration": 180 * 45, "users": 0, "spawn_rate": 1},

    {"duration": 180 * 46, "users": 2, "spawn_rate": 1},
    {"duration": 180 * 47, "users": 5, "spawn_rate": 1},
    {"duration": 180 * 48, "users": 10, "spawn_rate": 2},
    {"duration": 180 * 49, "users": 0, "spawn_rate": 1},

    {"duration": 180 * 50, "users": 3, "spawn_rate": 1},
    {"duration": 180 * 51, "users": 7, "spawn_rate": 2},
    {"duration": 180 * 52, "users": 13, "spawn_rate": 3},
    {"duration": 180 * 53, "users": 0, "spawn_rate": 1},

    {"duration": 180 * 54, "users": 2, "spawn_rate": 1},
    {"duration": 180 * 55, "users": 4, "spawn_rate": 1},
    {"duration": 180 * 56, "users": 8, "spawn_rate": 2},
    {"duration": 180 * 57, "users": 0, "spawn_rate": 1},

    {"duration": 180 * 58, "users": 3, "spawn_rate": 1},
    {"duration": 180 * 59, "users": 6, "spawn_rate": 1},
    {"duration": 180 * 60, "users": 12, "spawn_rate": 2},
]

          

    def tick(self):
        global current_stage
        run_time = self.get_run_time()
        
        for idx, stage in enumerate(self.stages):
            if run_time < stage["duration"]:
                if current_stage != (idx + 1):
                  	#log into a text file
                    resp = requests.get(PROM_URL, params={'query': 'up'}, timeout=5)
                    if resp.status_code == 200 and "data" in resp.json():
                        try:
                            #log the stage
                            print(f"Stage {current_stage} is completed")
                            with open("stage_log.txt", "a") as f:
                                f.write(f"Stage {idx + 1} started at time {run_time:.2f} seconds\n")
                        except Exception as e:
                            print(f"Stage {current_stage} is completed")
                    else:
                        print(f"Prometheus stopped working. The final stage is {current_stage}")
                        return None
                    current_stage = idx + 1
                    
                return (stage["users"], stage["spawn_rate"])




# ======================
# Test Start Event
# ======================
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global current_stage
    startCollection()
    print("\n🚀 Load Test Started. Tracking Success/Failure per Stage.\n")

# ======================
# Final Test Summary
# ======================
@events.quitting.add_listener
def on_quitting(environment, **kwargs):
       
    stop_event.set()
    monitor_thread.join()
    print("\n🎉 Load test completed gracefully.\n")




def startCollection():
    print("Metric Collection Process Started")
    monitor_thread.start()



def get_sum(result_list):
    values = []
    for item in result_list:
        val = float(item["value"][1])
        values.append(val)
    return sum(values)

