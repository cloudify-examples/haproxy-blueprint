# HAProxy Example

This blueprint deploys a server with HAProxy installed on it. The create operation can be used to add and remove nodes to the haproxy backend.

_This example explains how to connect to a MySQL backend using HAProxy. Therefore, initially install the [mariadb example](https://github.com/cloudify-examples/mariadb-blueprint). Once that example is installed, continue below._


## Deploy your HAProxy frontend with the MariaDB backend:

```
cfy deployments outputs mariadb
Retrieving outputs for deployment mariadb...
 - "cluster_addresses":
     Description: Cluster Addresses
     Value: [u'192.168.121.10']
 - "master":
     Description: master node ip
     Value: 192.168.121.10
```

Now, install HAProxy:

#### For AWS run:

```shell
$ cfy install \
    https://github.com/cloudify-examples/haproxy-blueprint/archive/master.zip \
    -b haproxy \
    -n aws-blueprint.yaml
```


#### For Azure run:

```shell
$ cfy install \
    https://github.com/cloudify-examples/haproxy-blueprint/archive/master.zip \
    -b haproxy \
    -n azure-blueprint.yaml
```


#### For Openstack run:

```shell
$ cfy install \
    https://github.com/cloudify-examples/haproxy-blueprint/archive/master.zip \
    -b haproxy \
    -n openstack-blueprint.yaml
```

#### For GCP run:

```shell
$ cfy install \
    https://github.com/cloudify-examples/haproxy-blueprint/archive/master.zip \
    -b haproxy \
    -n gcp-blueprint.yaml
```

For example, your output should look like this:

```
cfy install haproxy-blueprint/openstack-blueprint.yaml -b haproxy -i application_ip=192.168.121.10
Uploading blueprint haproxy-blueprint/openstack-blueprint.yaml...
 openstack-bluepri... |################################################| 100.0%
Blueprint uploaded. The blueprint's id is haproxy
Creating new deployment from blueprint haproxy...
Deployment created. The deployment's id is haproxy
Executing workflow install on deployment haproxy [timeout=900 seconds]
```

When install is successful, get the public IP of the load balancer:

```
cfy deployments outputs haproxy
Retrieving outputs for deployment haproxy...
 - "ip":
     Description: Public IP Address
     Value: 10.239.2.116

```

## Test connection to MySQL:

```
telnet -e X 10.239.2.116 3306
Telnet escape character is 'X'.
Trying 10.239.1.60...
Connected to 10.239.1.60.
Escape character is 'X'.
Y
5.5.5-10.1.26-MariaDB%gW`Z#???e#xX0'mruscsmysql_native_passwordX
telnet> ^C
```

## Add Backends:

Scale the MariaDB Cluster:

```
  ::  cfy executions start scale -d mariadb -p scalable_entity_name=app_group
Executing workflow scale on deployment mariadb [timeout=900 seconds]
2017-09-26 07:54:22.707  CFY <mariadb> Starting 'scale' workflow execution
```

When the scale workflow has succeeded, check the updated cluster addresses:

```
cfy deployments outputs mariadb
Retrieving outputs for deployment mariadb...
 - "cluster_addresses":
     Description: Cluster Addresses
     Value: [u'192.168.121.10', u'192.168.121.12']
 - "master":
     Description: master node ip
     Value: 192.168.121.10
```

Next update the inputs/execute-operation.yaml.example file with the haproxy_configuration_updater node instance id, and the next backend private IP.

Example file:
```
node_instance_ids: haproxy_configuration_updater_hpjz09
operation: create
allow_kwargs_override: true
operation_kwargs:
  frontend_port: 3306
  update_backends:
    server2:
      address: 192.168.121.12
      port: 3306
      maxconn: 32

```

Now update the backends on the HAProxy configuration:

```
cfy executions start execute_operation -vv -d ha -p haproxy-blueprint/inputs/execute-operation.yaml.example
```
