from django.shortcuts import render


class Pair:
    def __init__(self):
        self.first = None
        self.second = None


def make_pairs(original_list):
    pairs = []

    for i in range(0, len(original_list), 2):
        pair = Pair()
        pair.first = original_list[i]
        if i+1 < len(original_list):
            pair.second = original_list[i+1]
            pairs.append(pair)

    return pairs


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

    operations_list = ProcessDefinitionsApi().processdefs_get()
    for ope in operations_list:
        impl = ProcessImplementationsApi().processimpls_id_get(id=ope.implementations[0])

        ope.implementation = impl

    operations_pairs = make_pairs()

    return render(request, "operations.html", {"operations_pairs": operations_pairs})
