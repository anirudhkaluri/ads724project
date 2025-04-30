import threading
import time
import requests
import random
import csv
import math
from itertools import zip_longest
from autoscaling_main import scaleNodes
import bisect
import pandas as pd
DURATION=30
REQUEST_INTERVAL=3
PROM_TIMEOUT=False
REQUEST_TIMEOUT=180
PROMETHEUS_TIMEOUT=600
start_barrier = threading.Barrier(2)
API_URL = "http://ac4095edb3b45497185fbdaefe0f85a0-1384676893.us-east-1.elb.amazonaws.com/vector/ask"
HEADERS = {"Content-Type": "application/json"}
START_TIME=time.time()
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

collected_memory = []
collected_cpu = []
time_array=[]
experiment_array=[]

QUERIES = [
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

# Metrics
lock = threading.Lock()
request_lock=threading.Lock()
total_requests = 0
failed_requests = 0
request_counter = 1

# Sub-thread: handles sending a single request
def handle_request(user_id, req_num):
    global total_requests, failed_requests
    print(f"Request {req_num} in user {user_id} created")
    try:
        print(f"[{user_id}:{req_num}] Sending request")
        query=random.choice(QUERIES)
        payload = {"input": query,"req_num":f"{user_id}:{req_num}"}
        response = requests.get(API_URL, headers=HEADERS, json=payload, timeout=REQUEST_TIMEOUT)
        print(f"[{user_id}:{req_num}] Response received")
        with request_lock:
            total_requests += 1
            if not response.ok:
                print(f"❌The status of {user_id}:{req_num} is not 200")
                failed_requests += 1
    except Exception as e:
        print(f"[{user_id}:{req_num}] Request failed with exception {e}")
        print(f"❌ In Exception The status of {user_id}:{req_num} is not 200")
        with request_lock:
            total_requests += 1
            failed_requests += 1

# Parent thread: spawns a sub-thread every p seconds
def user_loop(user_id,P_INTERVAL):
    print(f"User {user_id} created")
    try:
        global request_counter, START_TIME, DURATION
        request_thread_array=[]
        #start_barrier.wait()  
        while time.time() - START_TIME < DURATION:
            with lock:
                req_num = request_counter
                request_counter += 1
            # Spawn sub-thread to handle the request
            print(f"User thread {user_id} creating request")
            t = threading.Thread(target=handle_request, args=(user_id, req_num))
            t.start()
            request_thread_array.append(t)
            # Parent sleeps, unblocked by request handling
            time.sleep(P_INTERVAL)
        for count in range(len(request_thread_array)):
            print(f"Waiting for request {count} in {user_id} thread to join")
            request_thread_array[count].join()
        # for t in request_thread_array:
        #     t.join()
    except Exception as e:
        print(f'An exception occured in user_loop \n {e}')

def startResourcePressure(NUM_USERS,P_INTERVAL,node_count):
    print("Resource Pressure Process Started")
    threads = []
    global START_TIME, collected_memory, collected_cpu, total_requests, failed_requests, request_counter
    total_requests=0
    failed_requests=0
    request_counter=1
    stop_event = threading.Event()
    start_barrier = threading.Barrier(NUM_USERS)
    monitor_thread = threading.Thread(target=cpu_memory_monitor, args=(stop_event, 10, collected_cpu,collected_memory))
    monitor_thread.start()
    START_TIME= time.time()
    print("CREATING USER THREADS")
    for user_id in range(NUM_USERS):
        t = threading.Thread(target=user_loop, args=(user_id,P_INTERVAL))
        t.start()
        threads.append(t)

    for count in range(len(threads)):
        print(f"Waiting for {count} user thread to join")
        threads[count].join()

    print("ALL USER THREADS JOINED")
    stop_event.set()
    monitor_thread.join()
    END_TIME=START_TIME+DURATION
    metric_start_index=find_metric_index(START_TIME)
    metric_end_index=find_metric_index(END_TIME)
    cpu_avg=find_cpu_avg(metric_start_index,metric_end_index)
    mem_avg=find_mem_avg(metric_start_index,metric_end_index)
    print(f"\nTotal Users={NUM_USERS}, Request Interval={P_INTERVAL}")
    print(f"\nTotal requests sent: {total_requests}")
    print(f"Failed requests: {failed_requests}")
    print(f"Failure rate: {failed_requests / total_requests:.2%}")
    print(f"Average CPU={cpu_avg}")
    print(f"Average Memory={mem_avg}")
    temporary_array=[]
    temporary_array.append({'node_count':node_count,'request_sent_count':total_requests,'request_failed_count':failed_requests,'cpu_avg':cpu_avg,'memory_avg':mem_avg,'user_count':NUM_USERS,'request_interval':P_INTERVAL,'test_duration':DURATION})
    temporary_data_frame = pd.DataFrame(temporary_array)
    temporary_data_frame.to_csv("resource_pressure_data.csv", mode='a', header=not pd.io.common.file_exists("resource_pressure_data.csv"), index=False)

# def find_cpu_avg(start,end):
#     sublist = collected_cpu[start:end + 1]
#     total = sum(sublist)
#     average = total / len(sublist) if sublist else 0
#     return average

def find_cpu_avg(start, end):
    sublist = collected_cpu[start:end + 1]
    valid_values = [val for val in sublist if not math.isnan(val)]
    total = sum(valid_values)
    average = total / len(valid_values) if valid_values else 0
    return average


def find_mem_avg(start, end):
    sublist = collected_memory[start:end + 1]
    valid_values = [val for val in sublist if not math.isnan(val)]
    total = sum(valid_values)
    average = total / len(valid_values) if valid_values else 0
    return average


def find_metric_index(t):
    import bisect
    index=bisect.bisect_left(time_array,t)
    if index == len(time_array):
        index = -1
    return index 


def get_sum(result_list):
    values = []
    for item in result_list:
        val = float(item["value"][1])
        values.append(val)
    return sum(values)

def cpu_memory_monitor(stop_event, interval=10, collected_cpu=[], collected_memory=[]):
    while not stop_event.is_set():
        try:
            mem_resp = requests.get(PROM_URL, params={'query': MEMORY_QUERY})
            cpu_resp = requests.get(PROM_URL, params={'query': CPU_QUERY})
            mem_resp.raise_for_status()
            cpu_resp.raise_for_status()
            mem_data = mem_resp.json()
            cpu_data = cpu_resp.json()
        

            if mem_data["status"] == "success" and cpu_data["status"] == "success":
                mem_results = mem_data["data"]["result"]
                cpu_results = cpu_data["data"]["result"]
                mem_sum=get_sum(mem_results)
                cpu_sum=get_sum(cpu_results)
                collected_memory.append(mem_sum)
                collected_cpu.append(cpu_sum)
                time_array.append(time.time())
                print(f"[Monitor] CPU Usage: {cpu_sum:.2f} | Memory Usage: {mem_sum:.2f}")

            else:
                print("[Monitor] Error fetching data:") #, data.get("error", "Unknown error")

        except Exception as e:
            print(f"[Monitor] Error: Handle Exception")
            collected_memory.append(float('nan'))
            collected_cpu.append(float('nan'))
            time_array.append(time.time())


        time.sleep(interval)





for node_count in range(4,7):
    try:
            prometheus_start_time=time.time()
            print(f"TESTING FOR {node_count} NODES")
            scaleNodes(node_count)
            time.sleep(60)
            print(f"NODES SCALED TO {node_count} NODES")
            startResourcePressure(NUM_USERS,P_INTERVAL)
            wait_prometheus=True
            while wait_prometheus:
                if time.time()-prometheus_start_time>PROMETHEUS_TIMEOUT:
                    print(f"Prometheus Time Out Triggered")
                    PROM_TIMEOUT=True
                    break
                try:
                    resp = requests.get(PROM_URL, params={'query': 'up'}, timeout=5)
                    if resp.status_code == 200 and "data" in resp.json():
                        print("✅ Prometheus is back online.")
                        wait_prometheus=False
                        break
                except:
                    pass
                print(f"Waiting for prometheus after scaling....")
                time.sleep(5)
            for user_count in range(1,7):
                startResourcePressure(user_count,REQUEST_INTERVAL,node_count)
                print(f"Sleeping before next cycle starts")
                time.sleep(120)

    except Exception as e:
            print(f"Exception occured at global level {e}")
            print(f"Sleeping in global exception")
            time.sleep(120)


# experiment_data_frame = pd.DataFrame(experiment_array)
# experiment_data_frame.to_csv("resource_pressure_data.csv", mode='a', header=not pd.io.common.file_exists("resource_pressure_data.csv"), index=False)

# experiment_data_frame.to_csv("resource_pressure_data.csv")