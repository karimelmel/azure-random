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