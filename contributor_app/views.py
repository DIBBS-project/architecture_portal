import json
import logging

from common_dibbs.misc import configure_basic_authentication
from django.shortcuts import render

from common_dibbs.clients.ar_client.apis.appliance_implementations_api import ApplianceImplementationsApi
from common_dibbs.clients.ar_client.apis.appliances_api import AppliancesApi
from common_dibbs.clients.ar_client.apis.sites_api import SitesApi
from common_dibbs.clients.or_client.apis.operation_versions_api import OperationVersionsApi
from common_dibbs.clients.or_client.apis.operations_api import OperationsApi
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
    return redirect('contributor_operations')


def appliances(request, message_success=None):
    # Create a client for Appliances
    appliances_client = AppliancesApi()
    appliances_client.api_client.host = "%s" % (Settings().appliance_registry_url,)
    configure_basic_authentication(appliances_client, "admin", "pass")

    # Create a client for ApplianceImplementations
    appliance_implementations_client = ApplianceImplementationsApi()
    appliance_implementations_client.api_client.host = "%s" % (Settings().appliance_registry_url,)
    configure_basic_authentication(appliance_implementations_client, "admin", "pass")

    appliances_list = appliances_client.appliances_get()
    appliances_list2 = []
    for app in appliances_list:
        impls = []
        for impl_name in app.implementations:
            impl = appliance_implementations_client.appliances_impl_name_get(name=impl_name)
            impls.append(impl)

        app.implementations = impls
        if app.name != "common":
            appliances_list2.append(app)

    appliances_pairs = make_pairs(appliances_list2)

    return render(request, "appliances.html", {"appliances_pairs": appliances_pairs,
                                               "message_success": message_success})


def operations(request, message_success=None):
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
        if ope.implementations:
            impl = operation_versions_client.operationversions_id_get(id=ope.implementations[0])
            try:
                impl.output_parameters = make_keyval_pairs(json.loads(impl.output_parameters))
            except:
                logging.error("Could make keyval_pairs from this JSON string: '%s'" % (impl.output_parameters))
            ope.implementation = impl

        ope.string_parameters = json.loads(ope.string_parameters)
        ope.file_parameters = json.loads(ope.file_parameters)

    operations_pairs = make_pairs(operations_list)

    return render(request, "operations_contributor.html", {"operations_pairs": operations_pairs,
                                                           "message_success": message_success})


def operation_form(request, message_error=None):
    # Create a client for Appliances
    appliances_client = AppliancesApi()
    appliances_client.api_client.host = "%s" % (Settings().appliance_registry_url,)
    configure_basic_authentication(appliances_client, "admin", "pass")

    appliances_list = appliances_client.appliances_get()

    return render(request, "operation_form.html", {"appliances": appliances_list,
                                                   "message_error": message_error})


def operation_post(request):
    # Create a client for Operations
    operations_client = OperationsApi()
    operations_client.api_client.host = "%s" % (Settings().operation_registry_url,)
    configure_basic_authentication(operations_client, "admin", "pass")

    # Create a client for OperationVersions
    operation_versions_client = OperationVersionsApi()
    operation_versions_client.api_client.host = "%s" % (Settings().operation_registry_url,)
    configure_basic_authentication(operation_versions_client, "admin", "pass")

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

    if string_parameters == "":
        string_parameters = []

    if file_parameters == "":
        string_parameters = []

    definition_request_data = {
        "name": name,
        "logo_url": logo_url,
        "description": description,
        "string_parameters": string_parameters,
        "file_parameters": file_parameters
    }

    try:
        json.loads(string_parameters)
    except Exception as e:
        return operation_form(request, message_error="Error creating the operation definition: String parameters must be in JSON format")

    try:
        json.loads(file_parameters)
    except Exception as e:
        return operation_form(request, message_error="Error creating the operation definition: File parameters must be in JSON format")

    try:
        ret = operations_client.operations_post(data=definition_request_data)
        operation_id = ret.id
    except Exception as e:
        return operation_form(request, message_error="Error creating the operation definition: " + str(e))

    implementation_request_data = {
        "name": name + "_impl",
        "appliance": appliance,
        "operation": operation_id,
        "cwd": cwd,
        "script": script,
        "output_type": output_type,
        "output_parameters": output_parameters
    }

    try:
        operation_versions_client.operationversions_post(data=implementation_request_data)
        return operations(request, message_success="Successfully created operation #" + str(operation_id) + ".")
    except Exception as e:
        return operation_form(request, message_error="Error creating the operation implementation: " + str(e))


def appliance_form(request, message_error=None):
    return render(request, "appliance_form.html", {"message_error": message_error})


def appliance_post(request):
    name = request.POST.get('name')
    logo_url = request.POST.get('logo_url')
    description = request.POST.get('description')

    request_data = {
        "name": name,
        "logo_url": logo_url,
        "description": description,
    }

    # Create a client for Appliances
    appliances_client = AppliancesApi()
    appliances_client.api_client.host = "%s" % (Settings().appliance_registry_url,)
    configure_basic_authentication(appliances_client, "admin", "pass")

    try:
        ret = appliances_client.appliances_post(data=request_data)
        appliance_name = ret.name
        return appliances(request, message_success="Successfully created appliance '" + str(appliance_name) + "'.")
    except Exception as e:
        return appliance_form(request, message_error="Error creating the appliance: " + str(e))


def appliance_implementation_form(request, message_error=None):
    # Create a client for Appliances
    appliances_client = AppliancesApi()
    appliances_client.api_client.host = "%s" % (Settings().appliance_registry_url,)
    configure_basic_authentication(appliances_client, "admin", "pass")

    # Create a client for Sites
    sites_client = SitesApi()
    sites_client.api_client.host = "%s" % (Settings().appliance_registry_url,)
    configure_basic_authentication(sites_client, "admin", "pass")

    appliances_list = appliances_client.appliances_get()
    sites_list = sites_client.sites_get()

    default_appliance = request.GET.get('default_appliance')

    return render(request, "appliance_implementation_form.html", {"appliances": appliances_list,
                                                                  "sites": sites_list,
                                                                  "default_appliance": default_appliance,
                                                                  "message_error": message_error})


def appliance_implementation_post(request):
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

    # Create a client for ApplianceImplementations
    appliance_implementations_client = ApplianceImplementationsApi()
    appliance_implementations_client.api_client.host = "%s" % (Settings().appliance_registry_url,)
    configure_basic_authentication(appliance_implementations_client, "admin", "pass")

    try:
        ret = appliance_implementations_client.appliances_impl_post(data=request_data)
        appliance_impl_name = ret.name
        return appliances(
            request,
            message_success="Successfully created appliance implementation '" + str(appliance_impl_name) + "'."
        )
    except Exception as e:
        return appliance_implementation_form(request, message_error="Error creating the appliance: " + str(e))


def appliance_implementation_detail(request, appliance_impl_name):
    # Create a client for ApplianceImplementations
    appliance_implementations_client = ApplianceImplementationsApi()
    appliance_implementations_client.api_client.host = "%s" % (Settings().appliance_registry_url,)
    configure_basic_authentication(appliance_implementations_client, "admin", "pass")

    appliance_impl = appliance_implementations_client.appliances_impl_name_get(name=appliance_impl_name)

    return render(request, "appliance_implementation_detail.html", {"appliance_impl": appliance_impl})


def operation_detail(request, operation_id):
    # Create a client for Operations
    operations_client = OperationsApi()
    operations_client.api_client.host = "%s" % (Settings().operation_registry_url,)
    configure_basic_authentication(operations_client, "admin", "pass")

    # Create a client for OperationVersions
    operation_versions_client = OperationVersionsApi()
    operation_versions_client.api_client.host = "%s" % (Settings().operation_registry_url,)
    configure_basic_authentication(operation_versions_client, "admin", "pass")

    operation_def = operations_client.operations_id_get(operation_id)

    if operation_def.implementations:
        operation_impl = operation_versions_client.operationversions_id_get(operation_def.implementations[0])

        appliance = operation_impl.appliance
        cwd = operation_impl.cwd
        script = operation_impl.script
        output_type = operation_impl.name
        output_parameters = make_keyval_pairs(json.loads(operation_impl.output_parameters))
    else:
        appliance = None
        cwd = None
        script = None
        output_type = None
        output_parameters = None

    operation = {
        "name": operation_def.name,
        "logo_url": operation_def.logo_url,
        "id": operation_def.id,
        "appliance": appliance,
        "description": operation_def.description,
        "string_parameters": json.loads(operation_def.string_parameters),
        "file_parameters": json.loads(operation_def.file_parameters),
        "cwd": cwd,
        "script": script,
        "output_type": output_type,
        "output_parameters": output_parameters,
    }

    return render(request, "operation_detail.html", {"operation": operation})
