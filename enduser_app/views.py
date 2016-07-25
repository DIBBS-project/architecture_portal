from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import requests
import json

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
    from pr_client.apis.process_definitions_api import ProcessDefinitionsApi
    from pr_client.apis.process_implementations_api import ProcessImplementationsApi
    import json

    operations_list = ProcessDefinitionsApi().processdefs_get()

    for ope in operations_list:
        impl = ProcessImplementationsApi().processimpls_id_get(id=ope.implementations[0])
        impl.environment = make_keyval_pairs(json.loads(impl.environment))
        impl.output_parameters = make_keyval_pairs(json.loads(impl.output_parameters))
        impl.argv = json.loads(impl.argv)
        ope.implementation = impl

        ope.string_parameters = json.loads(ope.string_parameters)
        ope.file_parameters = json.loads(ope.file_parameters)

    operations_pairs = make_pairs(operations_list)

    return render(request, "operations_enduser.html", {"operations_pairs": operations_pairs})


def instances(request, message_success=None):
    import json
    from pd_client.apis.process_instances_api import ProcessInstancesApi
    from pr_client.apis.process_definitions_api import ProcessDefinitionsApi

    instances_list = ProcessInstancesApi().process_instances_get()
    for instance in instances_list:
        process = ProcessDefinitionsApi().processdefs_id_get(instance.process_definition_id)
        instance.process = process
        instance.logo_url = process.logo_url
        instance.parameters = make_keyval_pairs(json.loads(instance.parameters))
        instance.files = make_keyval_pairs(json.loads(instance.files))

    instances_pairs = make_pairs(instances_list)

    return render(request, "instances.html", {"operations_pairs": instances_pairs,
                                              "message_success": message_success})


def instances_operation(request, operation_id):
    import json
    from pd_client.apis.process_instances_api import ProcessInstancesApi
    from pr_client.apis.process_definitions_api import ProcessDefinitionsApi

    # The parameters parsed from a URL are given as strings
    operation_id = int(operation_id)

    instances_list = ProcessInstancesApi().process_instances_get()
    instances_list_operation = []
    for instance in instances_list:
        if instance.process_definition_id == operation_id:
            process = ProcessDefinitionsApi().processdefs_id_get(instance.process_definition_id)
            instance.process = process
            instance.logo_url = process.logo_url
            instance.parameters = make_keyval_pairs(json.loads(instance.parameters))
            instance.files = make_keyval_pairs(json.loads(instance.files))
            instances_list_operation.append(instance)

    instances_pairs = make_pairs(instances_list_operation)

    return render(request, "instances.html", {"operations_pairs": instances_pairs, "operation_id": operation_id})


def executions(request, message_success=None):
    from pd_client.apis.process_instances_api import ProcessInstancesApi
    from pr_client.apis.process_definitions_api import ProcessDefinitionsApi
    from pd_client.apis.executions_api import ExecutionsApi

    executions_list = ExecutionsApi().executions_get()
    for execution in executions_list:
        instance = ProcessInstancesApi().process_instances_id_get(execution.process_instance)
        process = ProcessDefinitionsApi().processdefs_id_get(instance.process_definition_id)
        execution.instance = instance
        instance.process = process

    return render(request, "executions.html", {"executions_list": executions_list,
                                               "message_success": message_success})


def run_execution(request, execution_id):
    import settings as global_settings

    run_process_url = "%s/exec/%s/run/" % (global_settings.Settings().process_dispatcher_url, execution_id)
    requests.get(run_process_url)

    data = serializers.serialize('json', {"status": "running"})
    return HttpResponse(data, content_type='application/json')


def instance_form(request, message_error=None):
    from pr_client.apis.process_definitions_api import ProcessDefinitionsApi

    operations_list = ProcessDefinitionsApi().processdefs_get()

    if request.GET.get('default_operation'):
        default_operation = int(request.GET.get('default_operation'))
    else:
        default_operation = None

    return render(request, "instance_form.html", {"operations": operations_list,
                                                  "default_operation": default_operation,
                                                  "message_error": message_error})


def instance_post(request):
    from pd_client.apis.process_instances_api import ProcessInstancesApi
    from pd_client.configure import configure_auth_basic

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

    configure_auth_basic("admin", "pass")
    try:
        ret = ProcessInstancesApi().process_instances_post(data=request_data)
        instance_id = ret.id
        return instances(request, message_success="Successfully created instance #" + str(instance_id) + ".")
    except Exception as e:
        return instance_form(request, message_error="Error creating the instance: " + str(e))


def execution_form(request, message_error=None):
    from pd_client.apis.process_instances_api import ProcessInstancesApi

    instances_list = ProcessInstancesApi().process_instances_get()

    if request.GET.get('default_instance'):
        default_instance = int(request.GET.get('default_instance'))
    else:
        default_instance = None

    return render(request, "execution_form.html", {"instances": instances_list,
                                                   "default_instance": default_instance,
                                                   "message_error": message_error})


def execution_post(request):
    from pd_client.apis.executions_api import ExecutionsApi
    from pd_client.configure import configure_auth_basic
    from rp_client.apis.users_api import UsersApi

    user = UsersApi().users_id_get(id=1)

    operation_instance = request.POST.get('operation_instance')
    callback_url = request.POST.get('callback_url')
    force_spawn_cluster = request.POST.get('force_spawn_cluster')

    request_data = {
        "process_instance": operation_instance,
        "resource_provisioner_token": user.api_token,
        "callback_url": callback_url,
    }

    if force_spawn_cluster:
        request_data["force_spawn_cluster"] = force_spawn_cluster

    configure_auth_basic("admin", "pass")
    try:
        ret = ExecutionsApi().executions_post(data=request_data)
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
    from rp_client.apis.cluster_definitions_api import ClusterDefinitionsApi

    clusters_list = ClusterDefinitionsApi().clusters_get()

    def extract_app(app):
        return {"name": app["name"], "progress": int(app["progress"])}

    for cluster in clusters_list:
        response = requests.get("http://%s:8088/ws/v1/cluster/apps" % (cluster.master_node_ip))
        response_json = json.loads(response.content)
        executions = map(lambda x: extract_app(x), response_json["apps"]["app"])
        running_executions = filter(lambda x: x["progress"] < 100, executions)
        cluster.running_executions = running_executions
        cluster.number_of_nodes = len(cluster.hosts_ips)

    # operations_pairs = make_pairs(operations_list)

    return render(request, "clusters.html", {"clusters_list": clusters_list})
