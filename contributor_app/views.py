from django.shortcuts import render


class Pair:
    def __init__(self):
        self.first = None
        self.second = None


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

    appliances_pairs = []

    for i in range(0, len(appliances_list), 2):
        pair = Pair()
        pair.first = appliances_list[i]
        if i+1 < len(appliances_list):
            pair.second = appliances_list[i+1]
        appliances_pairs.append(pair)

    return render(request, "appliances.html", {"appliances_pairs": appliances_pairs})


def operations(request):
    from pr_client.apis.process_definitions_api import ProcessDefinitionsApi
    from pr_client.apis.process_implementations_api import ProcessImplementationsApi

    operationsp = ProcessDefinitionsApi().processdefs_get()
    for ope in operationsp:
        impl = ProcessImplementationsApi().processimpls_id_get(id=ope.implementations[0])

        ope.implementation = impl

    return render(request, "operations.html", {"operations": operationsp})
