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


def index(request):
    from django.shortcuts import redirect
    return redirect('contributor_operations')


def appliances(request, message_success=None):
    from ar_client.apis.appliances_api import AppliancesApi
    from ar_client.apis.appliance_implementations_api import ApplianceImplementationsApi

    appliances_list = AppliancesApi().appliances_get()
    appliances_list2 = []
    for app in appliances_list:
        impls = []
        for impl_name in app.implementations:
            impl = ApplianceImplementationsApi().appliances_impl_name_get(name=impl_name)
            impls.append(impl)

        app.implementations = impls
        if app.name != "common":
            appliances_list2.append(app)

    appliances_pairs = make_pairs(appliances_list2)

    return render(request, "appliances.html", {"appliances_pairs": appliances_pairs,
                                               "message_success": message_success})


def operations(request, message_success=None):
    from or_client.apis.process_definitions_api import ProcessDefinitionsApi
    from or_client.apis.process_implementations_api import ProcessImplementationsApi
    import json

    operations_list = ProcessDefinitionsApi().processdefs_get()

    for ope in operations_list:
        impl = ProcessImplementationsApi().processimpls_id_get(id=ope.implementations[0])
        impl.output_parameters = make_keyval_pairs(json.loads(impl.output_parameters))
        ope.implementation = impl

        ope.string_parameters = json.loads(ope.string_parameters)
        ope.file_parameters = json.loads(ope.file_parameters)

    operations_pairs = make_pairs(operations_list)

    return render(request, "operations_contributor.html", {"operations_pairs": operations_pairs,
                                                           "message_success": message_success})


def operation_form(request, message_error=None):
    from ar_client.apis.appliances_api import AppliancesApi

    appliances_list = AppliancesApi().appliances_get()

    return render(request, "operation_form.html", {"appliances": appliances_list,
                                                   "message_error": message_error})


def operation_post(request):
    from or_client.apis.process_definitions_api import ProcessDefinitionsApi
    from or_client.apis.process_implementations_api import ProcessImplementationsApi
    from or_client.configure import configure_auth_basic

    name = request.POST.get('name')
    logo_url = request.POST.get('logo_url')
    description = request.POST.get('description')
    string_parameters = request.POST.get('string_parameters')
    file_parameters = request.POST.get('file_parameters')
    appliance = request.POST.get('appliance')
    cwd = request.POST.get('cwd')
    script = request.POST.get('script')
    output_type = request.POST.get('output_type')
    output_parameters = request.POST.get('output_parameters')

    configure_auth_basic("admin", "pass")

    definition_request_data = {
        "name": name,
        "logo_url": logo_url,
        "description": description,
        "string_parameters": string_parameters,
        "file_parameters": file_parameters
    }

    try:
        ret = ProcessDefinitionsApi().processdefs_post(data=definition_request_data)
        operation_id = ret.id
    except Exception as e:
        return operation_form(request, message_error="Error creating the operation definition: " + str(e))

    implementation_request_data = {
        "name": name + "_impl",
        "appliance": appliance,
        "process_definition": operation_id,
        "cwd": cwd,
        "script": script,
        "output_type": output_type,
        "output_parameters": output_parameters
    }

    try:
        ProcessImplementationsApi().processimpls_post(data=implementation_request_data)
        return operations(request, message_success="Successfully created operation #" + str(operation_id) + ".")
    except Exception as e:
        return operation_form(request, message_error="Error creating the operation implementation: " + str(e))


def appliance_form(request, message_error=None):

    return render(request, "appliance_form.html", {"message_error": message_error})


def appliance_post(request):
    from ar_client.apis.appliances_api import AppliancesApi
    from ar_client.configure import configure_auth_basic

    name = request.POST.get('name')
    logo_url = request.POST.get('logo_url')
    description = request.POST.get('description')

    request_data = {
        "name": name,
        "logo_url": logo_url,
        "description": description,
    }

    configure_auth_basic("admin", "pass")
    try:
        ret = AppliancesApi().appliances_post(data=request_data)
        appliance_name = ret.name
        return appliances(request, message_success="Successfully created appliance '" + str(appliance_name) + "'.")
    except Exception as e:
        return appliance_form(request, message_error="Error creating the appliance: " + str(e))


def appliance_implementation_form(request, message_error=None):
    from ar_client.apis.appliances_api import AppliancesApi
    from ar_client.apis.sites_api import SitesApi

    appliances_list = AppliancesApi().appliances_get()
    sites_list = SitesApi().sites_get()

    default_appliance = request.GET.get('default_appliance')

    return render(request, "appliance_implementation_form.html", {"appliances": appliances_list,
                                                                  "sites": sites_list,
                                                                  "default_appliance": default_appliance,
                                                                  "message_error": message_error})


def appliance_implementation_post(request):
    from ar_client.apis.appliance_implementations_api import ApplianceImplementationsApi
    from ar_client.configure import configure_auth_basic

    name = request.POST.get('name')
    logo_url = request.POST.get('logo_url')
    image_name = request.POST.get('image_name')
    site = request.POST.get('site')
    appliance = request.POST.get('appliance')

    request_data = {
        "name": name,
        "logo_url": logo_url,
        "image_name": image_name,
        "site": site,
        "appliance": appliance,
    }

    configure_auth_basic("admin", "pass")
    try:
        ret = ApplianceImplementationsApi().appliances_impl_post(data=request_data)
        appliance_impl_name = ret.name
        return appliances(
            request,
            message_success="Successfully created appliance implementation '" + str(appliance_impl_name) + "'."
        )
    except Exception as e:
        return appliance_implementation_form(request, message_error="Error creating the appliance: " + str(e))


def appliance_implementation_detail(request, appliance_impl_name):
    from ar_client.apis.appliance_implementations_api import ApplianceImplementationsApi

    appliance_impl = ApplianceImplementationsApi().appliances_impl_name_get(name=appliance_impl_name)

    return render(request, "appliance_implementation_detail.html", {"appliance_impl": appliance_impl})


def operation_detail(request, operation_id):
    import json
    from or_client.apis.process_definitions_api import ProcessDefinitionsApi
    from or_client.apis.process_implementations_api import ProcessImplementationsApi

    operation_def = ProcessDefinitionsApi().processdefs_id_get(operation_id)
    operation_impl = ProcessImplementationsApi().processimpls_id_get(operation_def.implementations[0])

    operation = {
        "name": operation_def.name,
        "logo_url": operation_def.logo_url,
        "id": operation_def.id,
        "appliance": operation_impl.appliance,
        "description": operation_def.description,
        "string_parameters": json.loads(operation_def.string_parameters),
        "file_parameters": json.loads(operation_def.file_parameters),
        "cwd": operation_impl.cwd,
        "script": operation_impl.script,
        "output_type": operation_impl.name,
        "output_parameters": make_keyval_pairs(json.loads(operation_impl.output_parameters)),
    }

    return render(request, "operation_detail.html", {"operation": operation})
