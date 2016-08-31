from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import requests
import json
from settings import Settings

import base64


def configure_basic_authentication(swagger_client, username, password):
    authentication_string = "%s:%s" % (username, password)
    base64_authentication_string = base64.b64encode(bytes(authentication_string))
    header_key = "Authorization"
    header_value = "Basic %s" % (base64_authentication_string, )
    swagger_client.api_client.default_headers[header_key] = header_value


def make_pairs(original_list):
    pairs = []

    for i in range(0, len(original_list), 2):
        pair = dict()
        pair["first"] = original_list[i]
        pair["second"] = original_list[i+1] if i+1 < len(original_list) else None
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
    from or_client.apis.operations_api import OperationsApi
    from or_client.apis.operation_versions_api import OperationVersionsApi
    import json

    # Create a client for Operations
    operations_client = OperationsApi()
    operations_client.api_client.host = "%s" % (Settings().operation_registry_url,)
    configure_basic_authentication(operations_client, "admin", "pass")

    # Create a client for OperationVersions
    operation_verions_client = OperationVersionsApi()
    operation_verions_client.api_client.host = "%s" % (Settings().operation_registry_url,)
    configure_basic_authentication(operation_verions_client, "admin", "pass")

    operations_list = operations_client.operations_get()

    for ope in operations_list:
        impl = operation_verions_client.operationversions_id_get(id=ope.implementations[0])
        impl.output_parameters = make_keyval_pairs(json.loads(impl.output_parameters))
        ope.implementation = impl

        ope.string_parameters = json.loads(ope.string_parameters)
        ope.file_parameters = json.loads(ope.file_parameters)

    operations_pairs = make_pairs(operations_list)

    return render(request, "operations_enduser.html", {"operations_pairs": operations_pairs})


def instances(request, message_success=None):
    import json
    from om_client.apis.instances_api import InstancesApi
    from or_client.apis.operations_api import OperationsApi

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
    import json
    from om_client.apis.instances_api import InstancesApi
    from or_client.apis.operations_api import OperationsApi

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
    from om_client.apis.instances_api import InstancesApi
    from om_client.apis.executions_api import ExecutionsApi
    from or_client.apis.operations_api import OperationsApi

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
    for execution in executions_list:
        instance = instances_client.instances_id_get(execution.operation_instance)
        process = operations_client.operations_id_get(instance.process_definition_id)
        execution.instance = instance
        instance.process = process

    return render(request, "executions.html", {"executions_list": executions_list,
                                               "message_success": message_success})


def run_execution(request, execution_id):
    import settings as global_settings

    run_process_url = "%s/exec/%s/run/" % (global_settings.Settings().operation_manager_url, execution_id)
    requests.get(run_process_url)

    return HttpResponse({"status": "running"}, content_type='application/json')


def instance_form(request, message_error=None):
    from or_client.apis.operations_api import OperationsApi

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
    from om_client.apis.instances_api import InstancesApi

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
    from om_client.apis.instances_api import InstancesApi

    # Create a client for OperationInstances
    instances_client = InstancesApi()
    instances_client.api_client.host = "%s" % (Settings().operation_manager_url,)
    configure_basic_authentication(instances_client, "admin", "pass")

    instances_list = instances_client.instances_get()

    if request.GET.get('default_instance'):
        default_instance = int(request.GET.get('default_instance'))
    else:
        default_instance = None

    return render(request, "execution_form.html", {"instances": instances_list,
                                                   "default_instance": default_instance,
                                                   "message_error": message_error})


def execution_post(request):
    from om_client.apis.executions_api import ExecutionsApi
    from rm_client.apis.users_api import UsersApi

    # Create a client for OperationExecutions
    executions_client = ExecutionsApi()
    executions_client.api_client.host = "%s" % (Settings().operation_manager_url,)
    configure_basic_authentication(executions_client, "admin", "pass")

    # TODO: Remove hardcoded once the central authentication system in place
    token_ret = UsersApi().api_token_auth_post({"username": "admin", "password": "pass"})
    token = token_ret.token

    operation_instance = request.POST.get('operation_instance')
    callback_url = request.POST.get('callback_url')
    force_spawn_cluster = request.POST.get('force_spawn_cluster')

    request_data = {
        "operation_instance": operation_instance,
        "resource_provisioner_token": token,
        "callback_url": callback_url,
    }

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
    from rm_client.apis.cluster_definitions_api import ClusterDefinitionsApi

    clusters_list = ClusterDefinitionsApi().clusters_get()

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
