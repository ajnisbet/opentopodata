# How to deploy on Kubernetes

This example shows how to deploy to Kubernetes using the base opentopodata docker image. It includes a workload (ingress.yml) configuration and a service (service.yml) configuration which is used to access the opentopodata API by routing queries to the container.

## Prerequisites

You need access to a K8s cluster and in this example we are using the command-line-interface `kubectl` to deploy. For instructions on how to do that visit [the K8s website](https://kubernetes.io/docs/tasks/tools/).

## Example

Assuming you have a domain, `subdomain.example.com` where you want to make the opentopodata available on the endpoint `subdomain.example.com/dem-api/`, the files [deployment.yml](./k8s/deployment.yml), [ingress.yml](./k8s/ingress.yml) and [service.yml](./k8s/service.yml) shows how to set that up. It works out of the box with the base opentopodata docker image.

Simply run these commands:

```sh
kubectl --namespace my-namespace apply -f service.yml
kubectl --namespace my-namespace apply -f ingress.yml
kubectl --namespace my-namespace apply -f deployment.yml
```

## service.yml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: dem-api
  labels:
    service: dem-api
spec:
  selector:
    deploy: dem-api
  ports:
    - port: 5000
      targetPort: 5000
```


## ingress.yml

```yaml
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: dem-api
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$1
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  rules:
  - host: subdomain.example.com
    http:
      paths:
      - path: /dem-api/(.*)
        backend:
          serviceName: dem-api
          servicePort: 5000
```

## deployment.yml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dem-api
spec:
  replicas: 1
  selector:
    matchLabels:
      deploy: dem-api
  template:
    metadata:
      labels:
        deploy: dem-api
    spec:
      containers:
        - image: opentopodata
          name: dem-api
          imagePullPolicy: Always
          ports:
            - containerPort: 5000

      restartPolicy: Always
```