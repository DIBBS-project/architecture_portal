from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
import requests

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


def instances(request):
    from pd_client.apis.process_instances_api import ProcessInstancesApi
    from pr_client.apis.process_definitions_api import ProcessDefinitionsApi

    instances_list = ProcessInstancesApi().process_instances_get()
    for instance in instances_list:
        process = ProcessDefinitionsApi().processdefs_id_get(instance.process_definition_id)
        instance.process = process

    instances_pairs = make_pairs(instances_list)

    return render(request, "instances.html", {"operations_pairs": instances_pairs})


def executions(request):
    from pd_client.apis.process_instances_api import ProcessInstancesApi
    from pr_client.apis.process_definitions_api import ProcessDefinitionsApi
    from pd_client.apis.executions_api import ExecutionsApi

    executions_list = ExecutionsApi().executions_get()
    for execution in executions_list:
        instance = ProcessInstancesApi().process_instances_id_get(execution.process_instance)
        process = ProcessDefinitionsApi().processdefs_id_get(instance.process_definition_id)
        execution.instance = instance
        instance.process = process

    return render(request, "executions.html", {"executions_list": executions_list})


def run_execution(request, execution_id):
    import settings as global_settings

    run_process_url = "%s/exec/%s/run/" % (global_settings.Settings().process_dispatcher_url, execution_id)
    requests.get(run_process_url)

    data = serializers.serialize('json', {"status": "running"})
    return HttpResponse(data, content_type='application/json')
