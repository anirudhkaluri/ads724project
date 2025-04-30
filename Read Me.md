
# FILES
The following are the brief descriptions of the files used:
## K8 FILES
* ./aws/ads-eks-cluster.yaml is the file that sets up the entire k8 cluster
* Dockerfile at  ./vector-experiment/Dockerfile containerized the web application that interfaces the LLM
* ./aws/vectorexp-deployment.yaml is used to deploy the django based web application
* ./aws/vectorservice.yaml is a service that exposes the web application
* ./aws/ollama-deployment.yaml deployment smollm:135m pods 
* ./aws/ollama-service.yaml is a k8 cluster service used by vectorexp-deployment (web application) pods to communicate with pods having ollama model


## EXPERIMENTATION AND RESULTS FILES
* ./aws/scaling_latency.py logs the time it is required to scale up/down 1,2,3,4,5,6,7 nodes/pods at 1:1 ratio for pods and nodes
* ./aws/upscaling.csv has the latency results for scaling up pods and nodes
* ./aws/downscaling.csv has the latency results for downscaling the pods and nodes
* ./aws/autoscaling.py is the basic autoscaling file that takes a command line input of a number n and scales down the nodes and pods in each deployment to n. It is not used anywhere.
* ./aws/resource_pressure.py creates artificial traffic under different conditions by varying the number of nodes and pods using the autoscaling_main.py script and collects SLO violations
* r./aws/esource_pressure_pods.py creates artificial traffic and collects the SLO violations under different conditions by varying just the pod count. Ultimately the output of this file has been used to build the resource presure model. 
* autoscaling_pods.py    
* ./aws/generate_cpu_load.py is a locust based load generation file that creates artificial traffic to our application. It outputs a file cpu_usage_data.csv
* ./aws/stage_log.txt logs the time it took to simulate each stage of traffic generation in the generate_cpu_load.py
* ./aws/cpu_usage_data_old.csv is the CPU usage collected by running the generate_cpu_load.py as a first experiment
* ./aws/cpu_usage_data_train.csv is the CPU usage collected by running the generate_cpu_load.py as a second experiment
* ./aws/cpu_usage_data_demo.csv is the CPU usage collected during the demo of this project
* ./aws/upscaling_pod_latency.csv is a file that is generated during resource pressure modelling to measure the latency for upscaling additional pods

##  MACHINE LEARNING
* old_lstm_model.h5 is the lsmt model that was built to predict cpu usage into the future.
* RP_FINAL_MODEL.ipynb is used to build the resource pressure model.


## FINAL FILES
* final_integration.py is the ultimate file that tracks the CPU usage, feeds it to the LSTM model which predicts the CPU, which then uses the Resource Pressure model that outputs the number of nodes/pods needed which then performs the autoscaling.
* final_integration_threads.py handles 2 conflicting autoscaling decisions


# PROCEDURE

* Create a cluster using eksctl and the configuration as given in ads-eks-cluster.yaml
* Create an AWS ECR instance to store the image of the web application that the EKS cluster uses. 
* Initialize a AWS RDS Postgres instance and ensure that the instance is on the same security group as the node group created in the above cluster
* Install prometheus on the eks cluster
* Execute the following command to create a docker image of the web application
    $docker build --platform linux/amd64 -t vectorexp . 
* Execute the following command to create a tag for the docker image created
    $docker tag vectorexp:latest 982534389010.dkr.ecr.us-east-1.amazonaws.com/adsproject:latest
* Execute the following command to push the docker image to AWS ECR
    $docker push <ECR_INSTANCE_CREATED>/adsproject:latest
* Deploy the ollama-service.yaml and vectorservice.yaml services
* Deploy the ollama-deployment.yaml and vectorexp-deployment.yaml files to create corresponding pods


At this point the infrastructure is set up

* generate_cpu_load.py will create cpu load and store the data in csv file
* While the traffic is being generated execute final_integration.py to run the autoscaling scripts based on the traffic load