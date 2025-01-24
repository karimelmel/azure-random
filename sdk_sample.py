from azure.identity import ClientSecretCredential
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.core.exceptions import HttpResponseError
from typing import List, Dict
import config

class AzureAuthClient:
    """
    Azure Authentication Client using service principal credentials.
    """
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        """
        Initialize the Azure auth client with service principal credentials.

        Args:
            tenant_id (str): Azure AD tenant ID
            client_id (str): Service principal client ID (application ID)
            client_secret (str): Service principal secret
        """
        self.credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )

def get_sub_role_assignment(subscription: str, tenant_id: str, client_id: str, client_secret: str) -> List[Dict]:
    """
    Fetch the list of role assignments for a specific subscription using the Azure SDK.

    Args:
        subscription (str): The subscription ID to fetch role assignments for
        tenant_id (str): Azure AD tenant ID
        client_id (str): Service principal client ID (application ID)
        client_secret (str): Service principal secret

    Returns:
        List[Dict]: A list of dictionaries containing the role assignment details
    """
    try:
        # Initialize the auth client
        auth_client = AzureAuthClient(tenant_id, client_id, client_secret)
        
        # Initialize the Authorization Management Client
        mgmt_client = AuthorizationManagementClient(
            credential=auth_client.credential,
            subscription_id=subscription.strip('/')  # Remove any trailing slashes
        )

        # Get all role assignments at subscription scope
        assignments = list(mgmt_client.role_assignments.list_for_subscription())
        
        # Return the raw assignments without converting to dict to preserve object properties
        return assignments
        
    except HttpResponseError as e:
        print(f"Error fetching subscription role assignments: {e.status_code} - {e.message}")
        return []
    except Exception as e:
        print(f"Unexpected error fetching role assignments: {str(e)}")
        return []

def main():
    """
    Main function to demonstrate usage.
    """
    # Get credentials from config file
    tenant_id = config.TENANT_ID
    client_id = config.CLIENT_ID
    client_secret = config.CLIENT_SECRET
    subscription_id = config.SUBSCRIPTION_ID

    if not all([tenant_id, client_id, client_secret, subscription_id]):
        raise ValueError(
            "Missing required configuration values. Please check your config.py file for: "
            "TENANT_ID, CLIENT_ID, CLIENT_SECRET, SUBSCRIPTION_ID"
        )

    # Get role assignments
    assignments = get_sub_role_assignment(
        subscription=subscription_id,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )

    # Print results using direct property access instead of dictionary access
    for assignment in assignments:
        print(f"Role Assignment ID: {assignment.name}")
        print(f"Principal ID: {assignment.principal_id}")
        print(f"Role Definition ID: {assignment.role_definition_id}")
        print("---")

if __name__ == "__main__":
    main()