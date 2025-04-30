echo "Starting to monitor node metrics every 2 seconds..."
echo "Press Ctrl+C to stop."

while true
do
    
    kubectl top nodes --no-headers | awk '{sum+=$3} END {print "Average CPU%:", sum/NR "%"}'

    sleep 5
done
