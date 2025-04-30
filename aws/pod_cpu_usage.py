#This file collects the CPU usage of each pod 
#That is running in the cluster
# $python pod_cpu_usage.py
import subprocess
import csv
import time
from datetime import datetime
import os

csv_file = 'pod_cpu_usage.csv'
pod_names = []

# Get the list of pods (just once)
result = subprocess.run(['kubectl', 'top', 'pod'], stdout=subprocess.PIPE)
output = result.stdout.decode('utf-8').strip().split('\n')
pod_names = [line.split()[0] for line in output[1:]]

# Check if CSV exists, else create with headers
if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        headers = ['timestamp'] + pod_names
        writer.writerow(headers)

try:
    while True:
        # Run 'kubectl top pod'
        result = subprocess.run(['kubectl', 'top', 'pod'], stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8').strip().split('\n')

        current_time = datetime.now().isoformat()
        row = [current_time]

        # Create a dictionary of pod CPU usage
        cpu_usage = {line.split()[0]: int(line.split()[1].rstrip('m')) for line in output[1:]}

        # Append CPU usage in pod order
        for pod in pod_names:
            row.append(cpu_usage.get(pod, 0))  # 0 if pod missing

        # Append row to CSV
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)

        print(f"[{current_time}] Logged CPU usage.")
        time.sleep(10)

except KeyboardInterrupt:
    print("\nMonitoring stopped.")


