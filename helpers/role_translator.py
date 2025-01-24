import json
from helpers.roles import azure_roles

class RoleTranslator:
    def __init__(self):
        self.role_mappings = azure_roles

    def extract_role_id(self, role_definition_id):
        """Extract the GUID portion from the full role definition ID."""
        return role_definition_id.split('/')[-1]

    def get_role_name(self, role_definition_id):
        """
        Get the friendly name for a role definition ID.
        Returns the friendly name or 'Unknown Role (guid)' if not found.
        """
        guid = self.extract_role_id(role_definition_id)
        return self.role_mappings.get(guid, f"Unknown Role ({guid})")

    def process_role_assignments(self, input_file, output_file):
        """
        Process role assignments JSON file and add friendly names.
        
        Args:
            input_file (str): Path to input JSON file
            output_file (str): Path to output JSON file
        """
        try:
            # Read the JSON file
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            # Process each role assignment
            for assignment in data:
                if 'properties' in assignment and 'roleDefinitionId' in assignment['properties']:
                    role_id = assignment['properties']['roleDefinitionId']
                    friendly_name = self.get_role_name(role_id)
                    assignment['properties']['roleName'] = friendly_name
            
            # Write the processed data to output file
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            print(f"Successfully processed role assignments and saved to {output_file}")
            
        except FileNotFoundError:
            print(f"Error: Could not find input file {input_file}")
            raise
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {input_file}")
            raise
        except Exception as e:
            print(f"Error: An unexpected error occurred: {str(e)}")
            raise