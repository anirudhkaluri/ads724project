#!/bin/bash

# Get pod names for vectorexp-deployment
pods=$(kubectl get pods -l app=vectorexp -o jsonpath='{.items[*].metadata.name}')

# Iterate through each pod and get logs
for pod in $pods; do
    echo "================ Logs for pod: $pod ================"
    kubectl logs "$pod"
    echo "===================================================="
    echo ""
done

