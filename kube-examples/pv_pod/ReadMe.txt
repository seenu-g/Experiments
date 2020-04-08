Steps to access PersistentVolumeclaim
Step 1: Create storage by going to shell
minikube ssh
$ sudo mkdir /mnt/data
$ cd /mnt/data
$ pwd   # verify directory /mnt/data
$ sudo sh -c "echo 'Hello from Kubernetes storage' > /mnt/data/index.html"
$ cat /mnt/data/index.html

Step 2 : Setup pods in minikube
kubectl apply -f pv-volume.yaml 
kubectl get pv task-pv-volume

kubectl apply -f pv-claim.yaml
kubectl get pv task-pv-volume
kubectl get pvc task-pv-claim
kubectl apply -f pv-pod.yaml
kubectl get pod task-pv-pod

kubectl get events --all-namespaces  --sort-by='.metadata.creationTimestamp'

Step 3: Run pod and see stored data
kubectl exec -it task-pv-pod -- /bin/bash

Run these commands in shell
apt update
apt install curl
curl http://localhost/

Step 4: Clean pods and storage setup by  going to shell

kubectl delete pod task-pv-pod
kubectl delete pvc task-pv-claim
kubectl delete pv task-pv-volume

minikube ssh
sudo rm /mnt/data/index.html
sudo rmdir /mnt/data