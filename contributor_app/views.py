from django.shortcuts import render


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


def appliances(request):
    from ar_client.apis.appliances_api import AppliancesApi
    from ar_client.apis.appliance_implementations_api import ApplianceImplementationsApi

    appliances_list = AppliancesApi().appliances_get()
    for app in appliances_list:
        impls = []
        for impl_name in app.implementations:
            impl = ApplianceImplementationsApi().appliances_impl_name_get(name=impl_name)
            impls.append(impl)

        app.implementations = impls

    appliances_pairs = make_pairs(appliances_list)

    return render(request, "appliances.html", {"appliances_pairs": appliances_pairs})


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

    return render(request, "operations_contributor.html", {"operations_pairs": operations_pairs})


def clusters(request):
    from rp_client.apis.cluster_definitions_api import ClusterDefinitionsApi


    clusters_list = ClusterDefinitionsApi().clusters_get()

    for cluster in clusters_list:
        cluster.number_of_nodes = len(cluster.hosts_ips)
        # appliance = cluster.appliance

    # operations_pairs = make_pairs(operations_list)

    return render(request, "clusters.html", {"clusters_list": clusters_list})


def operation_form(request):
    from ar_client.apis.appliances_api import AppliancesApi

    appliances_list = AppliancesApi().appliances_get()

    return render(request, "operation_form.html", {"appliances": appliances_list})


def operation_post(request):
    print ("post")
    pass
