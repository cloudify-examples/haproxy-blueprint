# HAProxy Example

This blueprint deploys a server with HAProxy installed on it. The create operation can be used to add and remove nodes to the haproxy backend.

## Try it out:

```shell
cfy install nodecellar-auto-scale-auto-heal-blueprint/aws-blueprint.yaml -b nodecellar
```

Gather the private IPs of the node_js hosts. Use one of them as the first backend.

```
cfy install -vv haproxy-blueprint/aws-blueprint.yaml -b ha -i application_ip=10.10.1.64
```

You can ssh in and out of the haproxy host to see the update configuration between each step. The public IP is available:

```
cfy deployments outputs ha
```

Next update the inputs/execute-operation.yaml.example file with the haproxy_configuration_updater node instance id, and the next backend private IP.

```
cfy executions start execute_operation -vv -d ha -p haproxy-blueprint/inputs/execute-operation.yaml.example
```
