from django.shortcuts import render


# Create your views here.

def make_pairs(original_list):
    pairs = []

    for i in range(0, len(original_list), 2):
        pair = dict()
        pair["first"] = original_list[i]
        pair["second"] = original_list[i+1] if i+1 < len(original_list) else None
        pairs.append(pair)
    return pairs


def instances(request):
    from pd_client.apis.process_instances_api import ProcessInstancesApi
    from pr_client.apis.process_definitions_api import ProcessDefinitionsApi

    instances_list = ProcessInstancesApi().process_instances_get()
    for instance in instances_list:
        process = ProcessDefinitionsApi().processdefs_id_get(instance.process_definition_id)
        instance.process = process

    instances_pairs = make_pairs(instances_list)

    return render(request, "instances.html", {"operations_pairs": instances_pairs})
