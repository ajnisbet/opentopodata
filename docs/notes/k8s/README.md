# How to deploy on Kubernetes
The deployment uses the base opentopodata docker image and shows how to deploy to Kubernetes (K8s) This example includes a workload (ingress.yml) configuration and a service (service.yml) configuration which is used to access the opentopodata API by routing queries to the container.

## Prerequisites
You need access to a K8s cluster and in this example we are using the command-line-interface `kubectl` to deploy. For instructions on how to do that visit [the K8s website](https://kubernetes.io/docs/tasks/tools/).

## Example
Assuming you have a domain, `subdomain.example.com` where you want to make the opentopodata available on the endpoint `subdomain.example.com/dem-api/`, the files **deployment.yml**, **ingress.yml** and **service.yml** shows how to set that up. It works out of the box with the base opentopodata docker image. Simply runs these commands:
```sh
kubectl --namespace my-namespace apply -f service.yml
kubectl --namespace my-namespace apply -f ingress.yml
kubectl --namespace my-namespace apply -f deployment.yml
```