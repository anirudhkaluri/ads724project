# FILES

## K8 FILES
* ads-eks-cluster.yaml is the file that sets up the entire k8 cluster
* Dockerfile at  ./vector-experiment/Dockerfile containerized the web application that interfaces the LLM
* vectorexp-deployment.yaml is used to deploy the django based web application
* vectorservice.yaml is a service that exposes the web application
* ollama-deployment.yaml deployment smollm:135m pods 
* ollama-service.yaml is a k8 cluster service used by vectorexp-deployment (web application) pods to communicate with pods having ollama model

## EXPERIMENTATION AND RESULTS FILES
* scaling_latency.py logs the time it is required to scale up/down 1,2,3,4,5,6,7 nodes/pods at 1:1 ratio for pods and nodes
* upscaling.csv has the latency results for scaling up pods and nodes
* downscaling.csv has the latency results for downscaling the pods and nodes
* autoscaling.py is the basic autoscaling file that takes a command line input of a number n and scales down the nodes and pods in each deployment to n. It is not used anywhere.
* resource_pressure.py creates artificial traffic under different conditions by varying the number of nodes and pods using the autoscaling_main.py script and collects SLO violations
* resource_pressure_pods.py creates artificial traffic and collects the SLO violations under different conditions by varying just the pod count. Ultimately the output of this file has been used to build the resource presure model. 
* autoscaling_pods.py    
* generate_cpu_load.py is a locust based load generation file that creates artificial traffic to our application. It outputs a file cpu_usage_data.csv
* stage_log.txt logs the time it took to simulate each stage of traffic generation in the generate_cpu_load.py
* cpu_usage_data_old.csv is the CPU usage collected by running the generate_cpu_load.py as a first experiment
* cpu_usage_data_train.csv is the CPU usage collected by running the generate_cpu_load.py as a second experiment
* cpu_usage_data_demo.csv is the CPU usage collected during the demo of this project
* upscaling_pod_latency.csv is a file that is generated during resource pressure modelling to measure the latency for upscaling additional pods

##  MACHINE LEARNING
* old_lstm_model.h5 is the lsmt model that was built to predict cpu usage into the future.
* RP_FINAL_MODEL.ipynb is used to build the resource pressure model.


## FINAL FILES
* final_integration.py is the ultimate file that tracks the CPU usage, feeds it to the LSTM model which predicts the CPU, which then uses the Resource Pressure model that outputs the number of nodes/pods needed which then performs the autoscaling.
* final_integration_threads.py handles 2 conflicting autoscaling decisions