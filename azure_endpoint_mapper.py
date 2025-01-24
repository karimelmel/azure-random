from azure.identity import ClientSecretCredential
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.apimanagement import ApiManagementClient
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.core.exceptions import HttpResponseError
from typing import Dict, List, Optional
import config

class AzureEndpointScanner:
    """Scanner for Azure public endpoints across different services."""
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, subscription_id: str):
        """Initialize with Azure credentials."""
        self.credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        self.subscription_id = subscription_id
        
        # Initialize service clients
        self.web_client = WebSiteManagementClient(self.credential, self.subscription_id)
        self.storage_client = StorageManagementClient(self.credential, self.subscription_id)
        self.sql_client = SqlManagementClient(self.credential, self.subscription_id)
        self.aks_client = ContainerServiceClient(self.credential, self.subscription_id)
        self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)
        self.apim_client = ApiManagementClient(self.credential, self.subscription_id)
        self.aci_client = ContainerInstanceManagementClient(self.credential, self.subscription_id)
        self.acr_client = ContainerRegistryManagementClient(self.credential, self.subscription_id)
        self.cosmos_client = CosmosDBManagementClient(self.credential, self.subscription_id)
        self.keyvault_client = KeyVaultManagementClient(self.credential, self.subscription_id)
        self.network_client = NetworkManagementClient(self.credential, self.subscription_id)

    def get_app_services(self) -> List[Dict]:
        """Get all App Service public endpoints."""
        endpoints = []
        try:
            web_apps = self.web_client.web_apps.list()
            for app in web_apps:
                if app.enabled and not app.client_cert_enabled:
                    endpoints.append({
                        'service_type': 'App Service',
                        'name': app.name,
                        'resource_group': app.resource_group,
                        'url': f"https://{app.default_host_name}",
                        'kind': app.kind
                    })
        except Exception as e:
            print(f"Error fetching App Services: {str(e)}")
        return endpoints

    def get_function_apps(self) -> List[Dict]:
        """Get all Function App public endpoints."""
        endpoints = []
        try:
            function_apps = self.web_client.web_apps.list()
            for app in function_apps:
                if app.kind and 'functionapp' in app.kind.lower():
                    endpoints.append({
                        'service_type': 'Function App',
                        'name': app.name,
                        'resource_group': app.resource_group,
                        'url': f"https://{app.default_host_name}",
                        'kind': app.kind
                    })
        except Exception as e:
            print(f"Error fetching Function Apps: {str(e)}")
        return endpoints

    def get_storage_accounts(self) -> List[Dict]:
        """Get all public Storage Account endpoints."""
        endpoints = []
        try:
            storage_accounts = self.storage_client.storage_accounts.list()
            for account in storage_accounts:
                if account.enable_https_traffic_only:
                    if account.primary_endpoints.blob:
                        endpoints.append({
                            'service_type': 'Storage Account (Blob)',
                            'name': account.name,
                            'resource_group': account.id.split('/')[4],
                            'url': account.primary_endpoints.blob,
                            'kind': account.kind
                        })
                    if account.primary_endpoints.file:
                        endpoints.append({
                            'service_type': 'Storage Account (File)',
                            'name': account.name,
                            'resource_group': account.id.split('/')[4],
                            'url': account.primary_endpoints.file,
                            'kind': account.kind
                        })
                    if account.primary_endpoints.table:
                        endpoints.append({
                            'service_type': 'Storage Account (Table)',
                            'name': account.name,
                            'resource_group': account.id.split('/')[4],
                            'url': account.primary_endpoints.table,
                            'kind': account.kind
                        })
        except Exception as e:
            print(f"Error fetching Storage Accounts: {str(e)}")
        return endpoints

    def get_api_management(self) -> List[Dict]:
        """Get all API Management service endpoints."""
        endpoints = []
        try:
            apim_services = self.apim_client.api_management_service.list()
            for service in apim_services:
                if service.public_ip_addresses:  # Check if public IP is enabled
                    endpoints.append({
                        'service_type': 'API Management',
                        'name': service.name,
                        'resource_group': service.id.split('/')[4],
                        'url': f"https://{service.gateway_url}",
                        'kind': service.sku.name
                    })
        except Exception as e:
            print(f"Error fetching API Management services: {str(e)}")
        return endpoints

    def get_container_instances(self) -> List[Dict]:
        """Get all Container Instances with public IP."""
        endpoints = []
        try:
            for rg in self.resource_client.resource_groups.list():
                containers = self.aci_client.container_groups.list_by_resource_group(rg.name)
                for container in containers:
                    if container.ip_address and container.ip_address.type == 'Public':
                        endpoints.append({
                            'service_type': 'Container Instance',
                            'name': container.name,
                            'resource_group': rg.name,
                            'url': f"{container.ip_address.ip}",
                            'kind': 'container'
                        })
        except Exception as e:
            print(f"Error fetching Container Instances: {str(e)}")
        return endpoints

    def get_container_registries(self) -> List[Dict]:
        """Get all Container Registry endpoints."""
        endpoints = []
        try:
            registries = self.acr_client.registries.list()
            for registry in registries:
                endpoints.append({
                    'service_type': 'Container Registry',
                    'name': registry.name,
                    'resource_group': registry.id.split('/')[4],
                    'url': f"https://{registry.login_server}",
                    'kind': registry.sku.name
                })
        except Exception as e:
            print(f"Error fetching Container Registries: {str(e)}")
        return endpoints

    def get_cosmos_db(self) -> List[Dict]:
        """Get all Cosmos DB endpoints."""
        endpoints = []
        try:
            accounts = self.cosmos_client.database_accounts.list()
            for account in accounts:
                if account.enable_public_network:
                    endpoints.append({
                        'service_type': 'Cosmos DB',
                        'name': account.name,
                        'resource_group': account.id.split('/')[4],
                        'url': f"https://{account.document_endpoint}",
                        'kind': account.kind
                    })
        except Exception as e:
            print(f"Error fetching Cosmos DB accounts: {str(e)}")
        return endpoints

    def get_key_vaults(self) -> List[Dict]:
            """Get all Key Vault endpoints."""
            endpoints = []
            try:
                vaults = self.keyvault_client.vaults.list()
                for vault in vaults:
                    is_public = True
                    if hasattr(vault, 'properties') and hasattr(vault.properties, 'network_acls'):
                        is_public = vault.properties.network_acls.default_action.lower() == 'allow'            
                    vault_uri = None
                    if hasattr(vault, 'properties') and hasattr(vault.properties, 'vault_uri'):
                        vault_uri = vault.properties.vault_uri
                    elif hasattr(vault, 'vault_uri'):
                        vault_uri = vault.vault_uri
                    else:
                        vault_uri = f"https://{vault.name}.vault.azure.net/"

                    if is_public:
                        endpoints.append({
                            'service_type': 'Key Vault',
                            'name': vault.name,
                            'resource_group': vault.id.split('/')[4],
                            'url': vault_uri,
                            'kind': 'vault'
                        })
            except Exception as e:
                print(f"Error fetching Key Vaults: {str(e)}")
                print(f"Full error details: {str(vars(e))}")  # Add more detailed error info
            return endpoints

    def get_application_gateways(self) -> List[Dict]:
        """Get all Application Gateway public endpoints."""
        endpoints = []
        try:
            gateways = self.network_client.application_gateways.list_all()
            for gateway in gateways:
                for frontend_ip in gateway.frontend_ip_configurations:
                    if hasattr(frontend_ip, 'public_ip_address') and frontend_ip.public_ip_address:
                        endpoints.append({
                            'service_type': 'Application Gateway',
                            'name': gateway.name,
                            'resource_group': gateway.id.split('/')[4],
                            'url': frontend_ip.public_ip_address.id,
                            'kind': gateway.sku.tier
                        })
        except Exception as e:
            print(f"Error fetching Application Gateways: {str(e)}")
        return endpoints

    def get_load_balancers(self) -> List[Dict]:
            """Get all Load Balancer public endpoints."""
            endpoints = []
            try:
                load_balancers = self.network_client.load_balancers.list_all()
                for lb in load_balancers:
                    for frontend_ip in lb.frontend_ip_configurations:
                        if hasattr(frontend_ip, 'public_ip_address') and frontend_ip.public_ip_address:
                            ip_resource_id = frontend_ip.public_ip_address.id
                            ip_name = ip_resource_id.split('/')[-1]
                            resource_group = ip_resource_id.split('/')[4]
                            
                            public_ip = self.network_client.public_ip_addresses.get(
                                resource_group_name=resource_group,
                                public_ip_address_name=ip_name
                            )
                            endpoints.append({
                                'service_type': 'Load Balancer',
                                'name': lb.name,
                                'resource_group': lb.id.split('/')[4],
                                'url': ip_resource_id,  # Keep the resource ID for reference
                                'ip_address': public_ip.ip_address
                            })
            except Exception as e:
                print(f"Error fetching Load Balancers: {str(e)}")
            return endpoints

def main():
    """Main function to scan and display all public endpoints."""
    # Get credentials from config file
    tenant_id = config.TENANT_ID
    client_id = config.CLIENT_ID
    client_secret = config.CLIENT_SECRET
    subscription_id = config.SUBSCRIPTION_ID

    scanner = AzureEndpointScanner(tenant_id, client_id, client_secret, subscription_id)
    
    # Collect all endpoints
    all_endpoints = []
    all_endpoints.extend(scanner.get_app_services())
    all_endpoints.extend(scanner.get_function_apps())
    all_endpoints.extend(scanner.get_storage_accounts())
    all_endpoints.extend(scanner.get_api_management())
    all_endpoints.extend(scanner.get_container_instances())
    all_endpoints.extend(scanner.get_container_registries())
    all_endpoints.extend(scanner.get_cosmos_db())
    all_endpoints.extend(scanner.get_key_vaults())
    all_endpoints.extend(scanner.get_application_gateways())
    all_endpoints.extend(scanner.get_load_balancers())

    # Group endpoints by service type
    endpoints_by_type = {}
    for endpoint in all_endpoints:
        service_type = endpoint['service_type']
        if service_type not in endpoints_by_type:
            endpoints_by_type[service_type] = []
        endpoints_by_type[service_type].append(endpoint)

    # Print results grouped by service type
    print("\nPublic Endpoints in Azure Subscription:\n")
    for service_type, endpoints in endpoints_by_type.items():
        print(f"\n{service_type} ({len(endpoints)} endpoints):")
        print("=" * 80)
        for endpoint in endpoints:
            print(f"Name: {endpoint['name']}")
            print(f"Resource Group: {endpoint['resource_group']}")
            print(f"URL: {endpoint['url']}")
            if service_type == 'Load Balancer' and 'ip_address' in endpoint:
                print(f"Public IP: {endpoint['ip_address']}")
            print("-" * 80)

    print(f"\nTotal public endpoints found: {len(all_endpoints)}")
    print("\nSummary by service type:")
    for service_type, endpoints in endpoints_by_type.items():
        print(f"{service_type}: {len(endpoints)} endpoint(s)")

if __name__ == "__main__":
    main()