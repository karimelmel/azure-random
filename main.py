import logging
from pprint import pprint
from typing import List, Dict
from helpers.auth import AuthClientGraph, AuthClientARM
from modules.graph_data import get_graph_data, get_federated_credentials
from modules.arm_data import (
    get_subscriptions,
    get_resource_groups,
    get_sub_role_assignment,
    get_rg_role_assignment,
    get_mg_role_assignment,
    get_management_groups,
    get_classic_admins,
    get_resources,
    get_resource_role_assignment,
    get_logic_apps_configuration,
)
import config
import json
from helpers.role_translator import RoleTranslator

# Constants
APP_ID = "appId"
ID = "id"
DISPLAY_NAME = "displayName"
PROPERTIES = "properties"
PRINCIPAL_ID = "principalId"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_data(auth_client, endpoint: str) -> List[Dict]:
    """
    Fetch data from a specified endpoint using the provided authentication client.

    Args:
        auth_client: The authentication client to use for fetching data.
        endpoint (str): The endpoint to fetch data from.

    Returns:
        List[Dict]: A list of dictionaries containing the fetched data.
    """
    try:
        data = get_graph_data(auth_client, endpoint)
        logger.info(f"Fetched data from {endpoint}")
        return data
    except Exception as e:
        logger.error(f"Error fetching data from {endpoint}: {str(e)}")
        return []


def get_service_principals(graph_auth_client: AuthClientGraph) -> Dict[str, str]:
    """
    Fetch service principals and create a lookup dictionary.

    Args:
        graph_auth_client (AuthClientGraph): The authentication client to use for fetching service principals.

    Returns:
        Dict[str, str]: A dictionary where the keys are application IDs and the values are service principal IDs.
    """
    service_principals = []
    service_principals = fetch_data(graph_auth_client, "servicePrincipals")
    return service_principals


def fetch_subscriptions(arm_auth_client: AuthClientARM) -> List[Dict]:
    # Fetch subscriptions
    subs = get_subscriptions(arm_auth_client)
    return subs


def fetch_role_assignments(
    arm_auth_client: AuthClientARM, subs: List[Dict]
) -> List[Dict]:
    """
    Fetch role assignments from ARM API for subscriptions, resource groups, and management groups.

    Args:
        arm_auth_client (AuthClientARM): The authentication client to use for fetching role assignments.
        subs (List[Dict]): A list of subscriptions.

    Returns:
        List[Dict]: A list of dictionaries representing role assignments.
    """
    role_assignments = []

    for sub in subs:
        sub_id = sub.get(ID)
        sub_role_assignments = get_sub_role_assignment(
            arm_auth_client, subscription=sub_id
        )
        role_assignments.extend(sub_role_assignments)

        rgs = get_resource_groups(arm_auth_client, subscription=sub_id)

        for rg in rgs:
            rg_id = rg.get(ID)
            rg_role_assignments = get_rg_role_assignment(
                arm_auth_client, subscription=sub_id, resource_group=rg_id
            )
            role_assignments.extend(rg_role_assignments)

    # Fetch management groups
    mgs = get_management_groups(arm_auth_client)

    for mg in mgs:
        mg_id = mg.get(ID)
        mg_role_assignments = get_mg_role_assignment(
            arm_auth_client, management_group=mg_id
        )
        role_assignments.extend(mg_role_assignments)

    return role_assignments


def fetch_all_resource_role_assignments(
    arm_auth_client: AuthClientARM, subs: List[Dict]
) -> List[Dict]:
    """
    Fetch role assignments for all resources within the subscriptions.

    Args:
        arm_auth_client (AuthClientARM): The authentication client to use for fetching role assignments.
        subs (List[Dict]): A list of subscriptions.

    Returns:
        List[Dict]: A list of dictionaries representing role assignments for all resources.
    """
    all_resource_role_assignments = []

    for sub in subs:
        sub_id = sub.get(ID)
        rgs = get_resource_groups(arm_auth_client, subscription=sub_id)

        for rg in rgs:
            rg_id = rg.get(ID)
            resources = get_resources(arm_auth_client, subscription=sub_id, resource_group=rg_id)

            for resource in resources:
                resource_id = resource.get(ID)
                resource_role_assignments = get_resource_role_assignment(
                    arm_auth_client, subscription=sub_id, resource_group=rg_id, resource=resource_id
                )
                all_resource_role_assignments.extend(resource_role_assignments)

    return all_resource_role_assignments


def fetch_classic_admins(
    arm_auth_client: AuthClientARM, subs: List[Dict]
) -> List[Dict]:
    classic_admins = []

    for sub in subs:
        sub_id = sub.get(ID)
        sub_classic_admins = get_classic_admins(arm_auth_client, subscription=sub_id)
        logger.info(
            f"Classic Administrators for subscription {sub_id}: {sub_classic_admins}"
        )
        classic_admins.extend(sub_classic_admins)

    return classic_admins

def fetch_logic_apps(arm_auth_client: AuthClientARM, subs: List[Dict]) -> List[Dict]:
    logic_apps = []
    for sub in subs:
        sub_id = sub.get(ID)
        rgs = get_resource_groups(arm_auth_client, subscription=sub_id)
        for rg in rgs:
            rg_id = rg.get(ID)
            logic_apps_config = get_logic_apps_configuration(arm_auth_client, subscription=sub_id, resource_group=rg_id)
            for logic_app in logic_apps_config:
                logic_app["subscriptionId"] = sub_id  # Add subscriptionId to each Logic App
            logic_apps.extend(logic_apps_config)
    return logic_apps

def main():
    """
    Main function to orchestrate the fetching and processing of data.
    """
    try:
        graph_auth_client = AuthClientGraph(
            config.CLIENT_ID, config.CLIENT_SECRET, config.TENANT_ID
        )
        arm_auth_client = AuthClientARM(
            config.CLIENT_ID, config.CLIENT_SECRET, config.TENANT_ID
        )

        logger.info("Fetching subscriptions...")
        subs = fetch_subscriptions(arm_auth_client)
        pprint(subs)
        with open("output/subscriptions.json", "w") as f:
            json.dump(subs, f)

        logger.info("Fetching role assignments...")
        role_assignments = fetch_role_assignments(arm_auth_client, subs)
        pprint(role_assignments)
        with open("output/role_assignments.json", "w") as f:
            json.dump(role_assignments, f)

        logger.info("Fetching all resource role assignments...")
        all_resource_role_assignments = fetch_all_resource_role_assignments(arm_auth_client, subs)
        pprint(all_resource_role_assignments)
        with open("output/all_resource_role_assignments.json", "w") as f:
            json.dump(all_resource_role_assignments, f)

        logger.info("Fetching classic administrators...")
        classic_admins = fetch_classic_admins(arm_auth_client, subs)
        pprint(classic_admins)
        with open("output/classic_admins.json", "w") as f:
            json.dump(classic_admins, f)

        logger.info("Fetching service principals...")
        service_principals = get_service_principals(graph_auth_client)
        pprint(service_principals)
        with open("output/service_principals.json", "w") as f:
            json.dump(service_principals, f)


        logger.info("Fetching Logic Apps configuration...")
        logic_apps = fetch_logic_apps(arm_auth_client, subs)
        pprint(logic_apps)
        with open("output/logic_apps.json", "w") as f:
            json.dump(logic_apps, f)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")


    translator = RoleTranslator()
    input_file = 'output/role_assignments.json'
    output_file = 'output/role_assignments_processed.json'
    try:
        translator.process_role_assignments(
            input_file, 
            output_file
        )
        
    except Exception as e:
        print(f"Error processing roles: {str(e)}")


if __name__ == "__main__":
    main()