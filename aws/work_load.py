import threading
import requests
import time
import random

import csv

import csv

from itertools import zip_longest

def save_results_to_csv(cpu_data,memory_data, latency_data, node_count, req_count, filename='results.csv'):
    # Clean CPU data: remove 'NAN' entries for calculations
    valid_cpu_data = [val for val in cpu_data if isinstance(val, (int, float))]
    valid_memory_data=[val for val in memory_data if isinstance(val, (int, float))]

    avg_cpu = sum(valid_cpu_data) / len(valid_cpu_data) if valid_cpu_data else 0
    avg_mem=sum(valid_memory_data) / len(valid_memory_data) if valid_memory_data else 0
    max_cpu = max(valid_cpu_data) if valid_cpu_data else 0 

    # Count failed requests in latency data
    failed_requests = latency_data.count('NAN')

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Write header row
        writer.writerow(['CPU Usage (%)', 'Latency (s)', 'Node Count', 'Request Count'])

        # Write data rows, filling missing values with 'NAN'
        for cpu, latency,memory in zip_longest(cpu_data, latency_data,memory_data, fillvalue='NAN'):
            writer.writerow([cpu, latency, memory, node_count, req_count])

        writer.writerow([])  # Empty row for stats

        # Write statistics
        writer.writerow(['Average CPU Usage (%)', avg_cpu])
        writer.writerow(['Average Memory usage',avg_mem])
        writer.writerow(['Max CPU Usage (%)', max_cpu])
        writer.writerow(['Failed Requests', failed_requests])

    print(f"✅ Results saved to {filename}")

# Prometheus endpoint and query
PROM_URL = "http://127.0.0.1:9090/api/v1/query"
PROM_QUERY = """

(
  (node_memory_MemTotal_bytes - node_memory_MemFree_bytes - node_memory_Cached_bytes - node_memory_Buffers_bytes)
  / node_memory_MemTotal_bytes
) * 100
or
(
  100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[15s])) * 100)
)
"""








# (
#   (node_memory_MemTotal_bytes - node_memory_MemFree_bytes)
#   / node_memory_MemTotal_bytes
# ) * 100
# or
# (
#   100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[30s])) * 100)
# )


""" def get_average(results):
    avg = []
    for result in results:
        avg.append(float(result["value"][1]))
    return avg  """

def get_average(results):
    avg = 0
    for result in results:
        avg += float(result["value"][1])
    return avg




def cpu_memory_monitor(stop_event, interval=5, collected_cpu=[], collected_memory=[]):
    while not stop_event.is_set():
        try:
            response = requests.get(PROM_URL, params={'query': PROM_QUERY})
            response.raise_for_status()
            data = response.json()

            if data["status"] == "success":
                results = data["data"]["result"]
                if results:
                    # Split results into memory and cpu based on count
                    total_results = len(results)
                    half = total_results // 2

                    memory_results = results[:half]
                    cpu_results = results[half:]

                    avg_memory = get_average(memory_results)
                    avg_cpu = get_average(cpu_results)

                    collected_memory.append(avg_memory)
                    collected_cpu.append(avg_cpu)

                    print(f"[Monitor] CPU Avg Usage: {avg_cpu:.2f}% | Memory Avg Usage: {avg_memory:.2f}%")
                else:
                    print("[Monitor] No results returned.")

            else:
                print("[Monitor] Error fetching data:", data.get("error", "Unknown error"))

        except Exception as e:
            print(f"[Monitor] Error: Handle Exception")

        time.sleep(interval)

#response_times is an array
#total_requests is the number of concurrent request
def simulate_variable_workload_mixed(api_url, total_requests, response_times):
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

    def make_request(query,req_number):
        try:
            headers = {"Content-Type": "application/json"}
            data = {"input": query,"req_num":req_number}
            start_time = time.time()
            print(f"#Request {req_number} |",'Query: ',query+" "+str(req_number),' Started.',start_time,flush=True)
            response = requests.get(api_url, headers=headers, json=data,timeout=2000)
            print(f"Request {req_number} response received",flush=True)
            elapsed_time = time.time() - start_time
            response_times.append(elapsed_time)
            print(f"Request {req_number} | ",
            "Status:", response.status_code, " | Time:",
             f"{elapsed_time:.3f}s", "| ","Successful response" if response.status_code == 200 else response.text, flush=True )
        except Exception as e:
            response_times.append('NAN')
            print(f"#Request {req_number} failed: {e}",flush=True)

    threads = []
    for k in range(total_requests):
        try:
            t = threading.Thread(target=make_request, args=(random.choice(queries),k))
            t.start()
            print(f"Thread for #request {k} started",flush=True)
            threads.append(t)
        except Exception as e:
            print(f"Thread creation for #request {k} failed:{e}",flush=True)

    for k in range(len(threads)):
        try:
            threads[k].join()
            print(f"Thread for #request {k} joined",flush=True)
        except Exception as e:
             print(f"The Thread waiting for #request {k} failed:{e}",flush=True)
    print("✅ All requests completed.")
    
   



"""    
def run_test_with_cpu_monitor(api_url, total_requests): 
    
    response_times = []

    print("✅ CPU Monitoring stopped.")
    print(f"📊 Collected {len(cpu_usages)} CPU samples.")
    print(f"📈 Collected {len(response_times)} response times.")
    return cpu_usages, response_times """


def run_test_with_node_count(node_count,api_url):
    stop_event = threading.Event()
    cpu_usages = []
    memory_usages=[]
    monitor_thread = threading.Thread(target=cpu_memory_monitor, args=(stop_event, 5, cpu_usages,memory_usages))
    monitor_thread.start()
    for i in range(20,(node_count+1)*20+1,20):
        #time.sleep(20)
        start_len_cpu=len(cpu_usages)
        start_len_memory=len(memory_usages)
        print('Start Len of CPU',start_len_cpu)
        response_times=[]
        print('START SIMULATING FOR ',i,' CONCURRENT REQUESTS')
        simulate_variable_workload_mixed(api_url, i, response_times)
        cpu_data=cpu_usages[start_len_cpu:]
        memory_data=memory_usages[start_len_memory:]
        print('END SIMULATING FOR',i,' CONCURRENT REQUESTS')
        time.sleep(10)
        result_csv_file='results_new_nodes_'+str(node_count)+'_req_'+str(i)+'.csv'
        print('Saving the csv....',result_csv_file)
        save_results_to_csv(cpu_data,memory_data,response_times, node_count,i,result_csv_file)
        print('Saving Done.....',result_csv_file)
        #wait until system is normal
        time.sleep(60)

    stop_event.set()
    monitor_thread.join()    


# Example test run
run_test_with_node_count(1,
    "http://ac4095edb3b45497185fbdaefe0f85a0-1384676893.us-east-1.elb.amazonaws.com/vector/ask"
)



