/* Kubernetes: Authentication, Authorization */
//Run 
minikube start
//View 
kubectl config view

//Create lfs158 namespace:
$ kubectl create namespace lfs158
//Create rbac directory and cd into it:
$ mkdir rbac
$ cd rbac/

//Create a private key for the student user with openssl tool, then create a certificate signing request for the student user
// with openssl tool:
~/rbac$ openssl genrsa -out student.key 2048
~/rbac$ openssl req -new -key student.key -out student.csr -subj "/CN=student/O=learner"
//Create a YAML configuration file for a certificate signing request object, and save it with a blank value for the request field: 
~/rbac$ vim signing-request.yaml
//View the certificate, encode it in base64, and assign it to the request field in the signing-request.yaml file:
~/rbac$ cat student.csr | base64 | tr -d '\n'

//assign it to the request field in the signing-request.yaml file:
~/rbac$ vim signing-request.yaml
//Create the certificate signing request object, then list the certificate signing request objects. It shows a pending state:
~/rbac$ kubectl create -f signing-request.yaml
~/rbac$ kubectl get csr
//Approve the certificate signing request object, then list the certificate signing request objects again. 
//It shows both approved and issued states:
~/rbac$ kubectl certificate approve student-csr
~/rbac$ kubectl get csr

//Extract the approved certificate from the certificate signing request, decode it with base64 and save it as a certificate file. 
//Then view the certificate in the newly created certificate file:
~/rbac$ kubectl get csr student-csr -o jsonpath='{.status.certificate}' | base64 --decode > student.crt
~/rbac$ cat student.crt
//Configure the student user's credentials by assigning the key and certificate: 
~/rbac$ kubectl config set-credentials student --client-certificate=student.crt --client-key=student.key

//Create a new context entry in the kubectl client's configuration file for the student user, associated with the 
//lfs158 namespace in the minikube cluster:
~/rbac$ kubectl config set-context student-context --cluster=minikube --namespace=lfs158 --user=student
//View the contents of the kubectl client's configuration file again, observing the new context entry student-context, 
//and the new user entry student:
~/rbac$ kubectl config view

//While in the default minikube context, create a new deployment in the lfs158 namespace:
~/rbac$ kubectl -n lfs158 create deployment nginx --image=nginx:alpine
//From the new context student-context try to list pods. The attempt fails because the student user has no permissions configured for the student-context:
~/rbac$ kubectl --context=student-context get pods

//Fobidden Error 
//The following steps will assign a limited set of permissions to the student user in the student-context. 
//Create a YAML configuration file for a pod-reader role object, which allows only get, watch, list actions in the 
//lfs158 namespace against pod objects. Then create the role object and list it from the default minikube context, but from 
//the lfs158 namespace:
~/rbac$ vim role.yaml
~/rbac$ kubectl create -f role.yaml
~/rbac$ kubectl -n lfs158 get roles

//Create a YAML configuration file for a rolebinding object, which assigns the permissions of the pod-reader role to the 
//student user. Then create the rolebinding object and list it from the default minikube context, but from the lfs158 namespace:
~/rbac$ vim rolebinding.yaml
~/rbac$ kubectl create -f rolebinding.yaml 
~/rbac$ kubectl -n lfs158 get rolebindings

//Now that we have assigned permissions to the student user, we can successfully list pods from the new context student-context.
~/rbac$ kubectl --context=student-context get pods
