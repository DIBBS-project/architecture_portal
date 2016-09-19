import json

import requests
from django.shortcuts import redirect
from common_dibbs.misc import configure_basic_authentication
from django.http import HttpResponse
from django.shortcuts import render

from common_dibbs.clients.om_client.apis.executions_api import ExecutionsApi
from common_dibbs.clients.om_client.apis.instances_api import InstancesApi
from common_dibbs.clients.or_client.apis.operation_versions_api import OperationVersionsApi
from common_dibbs.clients.or_client.apis.operations_api import OperationsApi
from common_dibbs.clients.rm_client.apis.cluster_definitions_api import ClusterDefinitionsApi
from common_dibbs.clients.rm_client.apis.host_definitions_api import HostDefinitionsApi
from common_dibbs.clients.rm_client.apis.users_api import UsersApi
from common_dibbs.clients.rm_client.apis.credentials_api import CredentialsApi
from settings import Settings


def make_pairs(original_list):
    pairs = []

    for i in range(0, len(original_list), 2):
        pair = dict()
        pair["first"] = original_list[i]
        pair["second"] = original_list[i + 1] if i + 1 < len(original_list) else None
        pairs.append(pair)
    return pairs


def make_keyval_pairs(original_dictionary):
    keyval_pairs = []
    for key, val in original_dictionary.items():
        keyval_pairs.append({"key": key, "val": val})

    return keyval_pairs


def index(request):
    from django.shortcuts import redirect
    return redirect('enduser_operations')


def operations(request):
    # Create a client for Operations
    operations_client = OperationsApi()
    operations_client.api_client.host = "%s" % (Settings().operation_registry_url,)
    configure_basic_authentication(operations_client, "admin", "pass")

    # Create a client for OperationVersions
    operation_versions_client = OperationVersionsApi()
    operation_versions_client.api_client.host = "%s" % (Settings().operation_registry_url,)
    configure_basic_authentication(operation_versions_client, "admin", "pass")

    operations_list = operations_client.operations_get()

    for ope in operations_list:
        impl = operation_versions_client.operationversions_id_get(id=ope.implementations[0])
        impl.output_parameters = make_keyval_pairs(json.loads(impl.output_parameters))
        ope.implementation = impl

        ope.string_parameters = json.loads(ope.string_parameters)
        ope.file_parameters = json.loads(ope.file_parameters)

    operations_pairs = make_pairs(operations_list)

    return render(request, "operations_enduser.html", {"operations_pairs": operations_pairs})


def instances(request, message_success=None):
    # Create a client for OperationInstances
    instances_client = InstancesApi()
    instances_client.api_client.host = "%s" % (Settings().operation_manager_url,)
    configure_basic_authentication(instances_client, "admin", "pass")

    # Create a client for Operations
    operations_client = OperationsApi()
    operations_client.api_client.host = "%s" % (Settings().operation_registry_url,)
    configure_basic_authentication(operations_client, "admin", "pass")

    instances_list = instances_client.instances_get()
    for instance in instances_list:
        process = operations_client.operations_id_get(instance.process_definition_id)
        instance.process = process
        instance.logo_url = process.logo_url
        instance.parameters = make_keyval_pairs(json.loads(instance.parameters))
        instance.files = make_keyval_pairs(json.loads(instance.files))

    instances_pairs = make_pairs(instances_list)

    return render(request, "instances.html", {"operations_pairs": instances_pairs,
                                              "message_success": message_success})


def instances_operation(request, operation_id):
    # Create a client for OperationInstances
    instances_client = InstancesApi()
    instances_client.api_client.host = "%s" % (Settings().operation_manager_url,)
    configure_basic_authentication(instances_client, "admin", "pass")

    # Create a client for Operations
    operations_client = OperationsApi()
    operations_client.api_client.host = "%s" % (Settings().operation_registry_url,)
    configure_basic_authentication(operations_client, "admin", "pass")

    # The parameters parsed from a URL are given as strings
    operation_id = int(operation_id)

    instances_list = instances_client.instances_get()
    instances_list_operation = []
    for instance in instances_list:
        if instance.process_definition_id == operation_id:
            process = operations_client.operations_id_get(instance.process_definition_id)
            instance.process = process
            instance.logo_url = process.logo_url
            instance.parameters = make_keyval_pairs(json.loads(instance.parameters))
            instance.files = make_keyval_pairs(json.loads(instance.files))
            instances_list_operation.append(instance)

    instances_pairs = make_pairs(instances_list_operation)

    return render(request, "instances.html", {"operations_pairs": instances_pairs, "operation_id": operation_id})


def executions(request, message_success=None):
    # Create a client for OperationInstances
    instances_client = InstancesApi()
    instances_client.api_client.host = "%s" % (Settings().operation_manager_url,)
    configure_basic_authentication(instances_client, "admin", "pass")

    # Create a client for OperationExecutions
    executions_client = ExecutionsApi()
    executions_client.api_client.host = "%s" % (Settings().operation_manager_url,)
    configure_basic_authentication(executions_client, "admin", "pass")

    # Create a client for Operations
    operations_client = OperationsApi()
    operations_client.api_client.host = "%s" % (Settings().operation_registry_url,)
    configure_basic_authentication(operations_client, "admin", "pass")

    executions_list = executions_client.executions_get()
    instances_list = instances_client.instances_get()
    processes_list = operations_client.operations_get()

    for execution in executions_list:
        instance_candidates = filter(lambda i: i.id == execution.operation_instance, instances_list)
        instance = instance_candidates[0] if instance_candidates else None
        process_candidates = filter(lambda e: instance is not None and e.id == instance.process_definition_id, processes_list)
        process = process_candidates[0] if process_candidates else None
        execution.instance = instance
        instance.process = process

    return render(request, "executions.html", {"executions_list": executions_list,
                                               "message_success": message_success})


def run_execution(request, execution_id):
    # Create a client for OperationExecutions
    executions_client = ExecutionsApi()
    executions_client.api_client.host = "%s" % (Settings().operation_manager_url,)
    configure_basic_authentication(executions_client, "admin", "pass")

    result = executions_client.exec_id_run_get(execution_id)

    return HttpResponse({"status": "running"}, content_type='application/json')


def instance_form(request, message_error=None):
    # Create a client for Operations
    operations_client = OperationsApi()
    operations_client.api_client.host = "%s" % (Settings().operation_registry_url,)
    configure_basic_authentication(operations_client, "admin", "pass")

    operations_list = operations_client.operations_get()

    if request.GET.get('default_operation'):
        default_operation = int(request.GET.get('default_operation'))
    else:
        default_operation = None

    return render(request, "instance_form.html", {"operations": operations_list,
                                                  "default_operation": default_operation,
                                                  "message_error": message_error})


def instance_post(request):
    # Create a client for OperationInstances
    instances_client = InstancesApi()
    instances_client.api_client.host = "%s" % (Settings().operation_manager_url,)
    configure_basic_authentication(instances_client, "admin", "pass")

    operation_id = request.POST.get('operation_id')
    name = request.POST.get('name')
    parameters = request.POST.get('parameters')
    files = request.POST.get('files')

    request_data = {
        "name": name,
        "process_definition_id": operation_id,
        "parameters": parameters,
        "files": files
    }

    try:
        ret = instances_client.instances_post(data=request_data)
        instance_id = ret.id
        return instances(request, message_success="Successfully created instance #" + str(instance_id) + ".")
    except Exception as e:
        return instance_form(request, message_error="Error creating the instance: " + str(e))


def execution_form(request, message_error=None):
    # Create a client for OperationInstances
    instances_client = InstancesApi()
    instances_client.api_client.host = "%s" % (Settings().operation_manager_url,)
    configure_basic_authentication(instances_client, "admin", "pass")

    # Create a client for Credentials
    credentials_client = CredentialsApi()
    credentials_client.api_client.host = "%s" % (Settings().resource_manager_url,)
    configure_basic_authentication(credentials_client, "admin", "pass")

    instances_list = instances_client.instances_get()
    credentials_list = credentials_client.credentials_get()

    if request.GET.get('default_instance'):
        default_instance = int(request.GET.get('default_instance'))
    else:
        default_instance = None

    return render(request, "execution_form.html", {"instances": instances_list,
                                                   "default_instance": default_instance,
                                                   "message_error": message_error,
                                                   "credentials": credentials_list})


def execution_post(request):
    # Create a client for OperationExecutions
    executions_client = ExecutionsApi()
    executions_client.api_client.host = "%s" % (Settings().operation_manager_url,)
    configure_basic_authentication(executions_client, "admin", "pass")

    # TODO: Remove hardcoded once the central authentication system in place
    # Create a client for Users
    users_client = UsersApi()
    users_client.api_client.host = "%s" % (Settings().resource_manager_url,)
    configure_basic_authentication(users_client, "admin", "pass")

    token_ret = users_client.api_token_auth_post({"username": "admin", "password": "pass"})
    token = token_ret.token

    operation_instance = request.POST.get('operation_instance')
    callback_url = request.POST.get('callback_url')
    force_spawn_cluster = request.POST.get('force_spawn_cluster')
    hint = request.POST.get('credential')

    request_data = {
        "operation_instance": operation_instance,
        "resource_provisioner_token": token,
        "callback_url": callback_url,
    }

    if hint is not None and hint != "Random":
        request_data["hints"] = """{"credentials": ["%s"]}""" % (hint)
    else:
        request_data["hints"] = """{"credentials": ["*"]}""" % (hint)

    if force_spawn_cluster:
        request_data["force_spawn_cluster"] = force_spawn_cluster

    try:
        ret = executions_client.executions_post(data=request_data)
        execution_id = ret.id

        # Makes the instance run at creation
        import threading
        import time
        thr = threading.Thread(target=run_execution, args=(request, execution_id))
        thr.start()
        time.sleep(2)

        return executions(request, message_success="Successfully created execution #" + str(execution_id) + ".")
    except Exception as e:
        return execution_form(request, message_error="Error creating the execution: " + str(e))


def clusters(request):
    # Create a client for ClusterDefinitions
    cluster_definitions_client = ClusterDefinitionsApi()
    cluster_definitions_client.api_client.host = "%s" % (Settings().resource_manager_url,)
    configure_basic_authentication(cluster_definitions_client, "admin", "pass")

    clusters_list = cluster_definitions_client.clusters_get()

    def extract_app(app):
        return {"name": app["name"], "progress": int(app["progress"])}

    for cluster in clusters_list:
        executions = []
        try:
            response = requests.get("http://%s:8088/ws/v1/cluster/apps" % (cluster.master_node_ip))
            response_json = json.loads(response.content)
            executions = map(lambda x: extract_app(x), response_json["apps"]["app"])
        except:
            executions = []
        running_executions = filter(lambda x: x["progress"] < 100, executions)
        cluster.running_executions = running_executions
        cluster.number_of_nodes = len(cluster.hosts_ips)

    # operations_pairs = make_pairs(operations_list)

    return render(request, "clusters.html", {"clusters_list": clusters_list})


def cluster_delete(request, cluster_id):
    # Create a client for ClusterDefinitions
    cluster_definitions_client = ClusterDefinitionsApi()
    cluster_definitions_client.api_client.host = "%s" % (Settings().resource_manager_url,)
    configure_basic_authentication(cluster_definitions_client, "admin", "pass")

    cluster_definitions_client.clusters_id_delete(cluster_id)

    return redirect("enduser_clusters")


def cluster_add_node(request, cluster_id):
    # Create a client for HostDefinitions
    host_definitions_client = HostDefinitionsApi()
    host_definitions_client.api_client.host = "%s" % (Settings().resource_manager_url,)
    configure_basic_authentication(host_definitions_client, "admin", "pass")

    host_definitions_client.hosts_post({"cluster_id": cluster_id})

    return redirect("enduser_clusters")


def cluster_remove_node(request, cluster_id):
    # Create a client for ClusterDefinitions
    cluster_definitions_client = ClusterDefinitionsApi()
    cluster_definitions_client.api_client.host = "%s" % (Settings().resource_manager_url,)
    configure_basic_authentication(cluster_definitions_client, "admin", "pass")

    # Create a client for HostDefinitions
    host_definitions_client = HostDefinitionsApi()
    host_definitions_client.api_client.host = "%s" % (Settings().resource_manager_url,)
    configure_basic_authentication(host_definitions_client, "admin", "pass")

    cluster = cluster_definitions_client.clusters_id_get(cluster_id)

    slaves_ids = filter(lambda h: str(h) != str(cluster.master_node_id), cluster.hosts_ids)
    if len(slaves_ids) > 0:
        host_definitions_client.hosts_id_delete(slaves_ids[0])

    return redirect("enduser_clusters")
