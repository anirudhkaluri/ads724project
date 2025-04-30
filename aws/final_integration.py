import requests
import numpy as np
import time
from datetime import datetime
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import MeanSquaredError
from sklearn.preprocessing import StandardScaler
import subprocess
import sys
import math
#NEW MODEL
# HISTORY_STEPS=10
# FUTURE_STEPS=5
# PREDICTED_INDEX=2

#OLD MODEL
HISTORY_STEPS=6
FUTURE_STEPS=3
PREDICTED_INDEX=2
CLUSTER_NAME = "ads-project-eks-cluster"
NODEGROUP_NAME = "ads-project-nodegroup-5"
DEPLOYMENT_NAME_APP = "vectorexp-deployment"
DEPLOYMENT_NAME_LLM = "ollama-deployment"
NAMESPACE = "default"
PODS_PER_NODE = 1
WAIT_TIMEOUT = 600   # Max wait time in seconds (10 minutes)
POLL_INTERVAL = 10

def scale_deployment(replicas):
    for deployment_name in [DEPLOYMENT_NAME_LLM]:
        print(f"Scaling deployment '{deployment_name}' to {replicas} pods...")
        cmd = [
            "kubectl", "scale",
            f"deployment/{deployment_name}",
            "--replicas", str(int(replicas)),
            "-n", NAMESPACE
        ]
        subprocess.run(cmd, check=True)
        print(f"✅ Deployment '{deployment_name}' asked to scale to {replicas} pods")

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
            if ready >= expected_replicas:
                print(f"\n✅ All {ready} pods for '{deployment_name}' are ready.")
                return
        except Exception:
            pass

        time.sleep(POLL_INTERVAL)

    print(f"\n❌ Timeout: Not all pods for '{deployment_name}' became ready in time.")
    sys.exit(1)

def get_llama_pod_count():
    cmd = [
                "kubectl", "get", "deployment", DEPLOYMENT_NAME_LLM,
                "-n", NAMESPACE,
                "-o", "jsonpath={.status.readyReplicas}"
            ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        ready = int(result.stdout.strip() or 0)
        return ready
    except Exception:
        pass 
# Load your trained LSTM model
model = load_model("old_lstm_model.h5", compile=False)
model.compile(optimizer=Adam(learning_rate=0.001), loss=MeanSquaredError())

# Initialize StandardScaler
scaler = StandardScaler()

# Prometheus server URL
PROMETHEUS_URL = 'http://localhost:9090'

# Function to query Prometheus and return sum of CPU usage across all instances
def get_total_cpu_usage():
    query = '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[30s])) * 100)'
    response = requests.get(f'{PROMETHEUS_URL}/api/v1/query', params={'query': query})
    results = response.json()
    
    if results['status'] == 'success':
        total_usage = sum(float(result['value'][1]) for result in results['data']['result'])
        return total_usage
    else:
        raise Exception("Failed to query Prometheus")

# Maintain a history of total CPU usage values
cpu_usage_history = []
scaler_fitted = False  # Flag to track if scaler is fitted yet

# Function to make a prediction
def make_prediction(input_sequence):
    global scaler
    # Scale input sequence
    input_sequence_scaled = scaler.transform(np.array(input_sequence).reshape(-1, 1))
    input_sequence_scaled = input_sequence_scaled.reshape((1, len(input_sequence), 1))
    
    # Predict
    prediction_scaled = model.predict(input_sequence_scaled)
    
    # Inverse transform predictions
    prediction_actual = scaler.inverse_transform(prediction_scaled.reshape(-1, 1)).flatten()
    return prediction_actual

# Function to perform online training
def online_train(input_seq, target_seq):
    global scaler
    
    # Scale input and target sequences
    X_train_scaled = scaler.transform(np.array(input_seq).reshape(-1, 1)).reshape((1, HISTORY_STEPS, 1))
    y_train_scaled = scaler.transform(np.array(target_seq).reshape(-1, 1)).reshape((1, FUTURE_STEPS))
    
    # Perform a single epoch of training
    model.fit(X_train_scaled, y_train_scaled, epochs=1, verbose=0)
    print(f"{datetime.now()}: Online model training completed on recent window.")

def rpModel(x):
    coefficients=[  -8.49894587 , 199.2504812  , -471.9632605 ,  291.65156642]
    degree=len(coefficients)
    ans=0
    for i in range(0,degree):
        ans= ans + (coefficients[i]*(x**i))
    return ans




# Live monitoring loop
def monitor_and_predict():
    global cpu_usage_history, scaler, scaler_fitted
    
    while True:
        total_cpu_usage = get_total_cpu_usage()
        print(f"{datetime.now()}: Total CPU Usage: {total_cpu_usage:.2f}")

        cpu_usage_history.append(total_cpu_usage)

        # Fit scaler after first 6 samples
        if not scaler_fitted and len(cpu_usage_history) >= HISTORY_STEPS:
            scaler.fit(np.array(cpu_usage_history[-HISTORY_STEPS:]).reshape(-1, 1))
            scaler_fitted = True
            print(f"{datetime.now()}: Scaler fitted with initial {HISTORY_STEPS} samples.")

        # Prediction when we have at least 6 samples and scaler is ready
        if scaler_fitted and len(cpu_usage_history) > HISTORY_STEPS:
            input_seq = cpu_usage_history[-HISTORY_STEPS:]
            predicted = make_prediction(input_seq)
            print("PREDICTING CPU USAGE")
            avg_predicted=predicted[PREDICTED_INDEX]
            print(f"CPU after {(PREDICTED_INDEX+1)*10}s={avg_predicted} using {input_seq}")
            #avg_predicted=sum(predicted)//len(predicted)
            pod_count=get_llama_pod_count()
            division=0

            if pod_count>0:
                rp_predicted=avg_predicted/(pod_count*100)
                predicted_failure_rate= rpModel(rp_predicted)
                #print(pod_count,division,pod_count*100)
                print(f"RP predicted={rp_predicted} ||| Faiure rate predicted={predicted_failure_rate}")
                if rp_predicted>0.206:
                    print('SCALE UP')
                    predicted_cpu_allocation= avg_predicted / 0.206
                    predicted_pod_count= int(math.ceil(predicted_cpu_allocation/(100)))
                    print(f"Predicted CPU Allocation required= {predicted_cpu_allocation}, Predicted Pod Count={predicted_pod_count}")
                    if predicted_pod_count>7:
                        print("Podcount predicted is higher. add nodes horizontally for further pod scaling")
                    else:
                        scale_deployment(min(predicted_pod_count,7))
                        wait_for_pods_ready(DEPLOYMENT_NAME_LLM,predicted_pod_count)
                        print('UPSCALING COMPLETE')
                elif pod_count>1:
                    print('SCALE DOWN')
                    scale_deployment(pod_count-1)
                    wait_for_pods_ready(DEPLOYMENT_NAME_LLM,pod_count-1)   
                    print('DOWNSCALING COMPLETE')    
                else:
                    print('No Scaling')      

        # Online training when we have at least 9 samples (6 input + 3 target)
        # if scaler_fitted and len(cpu_usage_history) >= HISTORY_STEPS+FUTURE_STEPS:
        #     print("Live training")
        #     input_seq = cpu_usage_history[-(HISTORY_STEPS+FUTURE_STEPS):-FUTURE_STEPS]
        #     target_seq = cpu_usage_history[-FUTURE_STEPS:]
        #     online_train(input_seq, target_seq) 

        # Poll every 10 seconds
        time.sleep(10)

if __name__ == "__main__":
    print("MONITORING STARTED")
    monitor_and_predict()
