import json
import subprocess
from typing import Tuple
from adore.optimization.api.file_based.direct_file_evaluators import JSONFileEvaluator
from adore.api.schema import *
from gnc import GNCCalculator


class GNCFileCMDEvaluator(JSONFileEvaluator):
    """
    Evaluate the GN&C architecture defined in the gnc.adore (or gnc_no_act.adore) model, using file-based evaluation.
    Here, we execute an external process to evaluate the architectures.
    """

    def _evaluate_file(self, input_file_path: str, output_file_path: str):
        # Executes gnc.py with input and output paths as arguments
        subprocess.check_output(['python', 'gnc.py', input_file_path, output_file_path])

    @classmethod
    def gnc_json_evaluate(cls, input_file: str, output_file: str):
        """Class method to show that the file evaluation process does not need anything in the instantiated evaluator"""

        # Load JSON input file
        with open(input_file, 'rb') as fp:
            data = json.load(fp)

        # Get element types
        sensor_types = cls._get_element_types(data, 'sensor')
        computer_types = cls._get_element_types(data, 'computer')
        actuator_types = cls._get_element_types(data, 'actuator')
        if len(actuator_types) == 0:  # Check if this model includes actuators
            actuator_types = None

        # Get element connections
        sensor_computer_conns = cls._get_element_connections(data, 'sensor', 'computer')
        computer_actuator_conns = None
        if actuator_types is not None:
            computer_actuator_conns = cls._get_element_connections(data, 'computer', 'actuator')

        # Calculate metrics
        for output_data in data['outputs']:
            if output_data['ref'] == 'mass':
                output_data['value'] = GNCCalculator.calc_mass(sensor_types, computer_types, actuator_types)
                output_data['units'] = 'kg'
            elif output_data['ref'] == 'failure-rate':
                output_data['value'] = GNCCalculator.calc_failure_rate(
                    sensor_types, computer_types, sensor_computer_conns, actuator_types, computer_actuator_conns)

        # Write JSON output file
        with open(output_file, 'wb') as fp:
            fp.write(json.dumps(data).encode('utf-8'))

    @staticmethod
    def _get_element_types(data, element_ref) -> List[str]:
        types = []
        for component_data in data['architecture']['system']['components']:
            # Match by component name
            if component_data['ref'] == element_ref:

                # Loop over instances
                for instance_data in component_data['instances']:

                    # Get type from attribute value
                    element_type = instance_data['attributes'][0]['values'][0]
                    assert element_type in ['A', 'B', 'C']

                    types.append(element_type)
        return types

    @staticmethod
    def _get_element_connections(data, src_ref: str, tgt_ref: str) -> List[Tuple[int, int]]:

        # First find all outgoing connections from source elements, and available connection targets
        connections = []
        conn_target_idx_map = {}
        for component_data in data['architecture']['system']['components']:
            # Match by source element
            if component_data['ref'] == src_ref:
                # Loop over component instances
                for instance_data in component_data['instances']:
                    # Loop over outgoing port connections
                    for out_port_connection_data in instance_data['outputPorts']:
                        # Loop over target connections
                        for target_id in out_port_connection_data['targetIds']:
                            connections.append((instance_data['index'], target_id))

            # Match by target element
            elif component_data['ref'] == tgt_ref:
                # Get available connection targets
                for instance_data in component_data['instances']:
                    for in_port_connection_data in instance_data['inputPorts']:
                        conn_target_idx_map[in_port_connection_data['id']] = instance_data['index']

        # Convert connection target IDs to instance indices
        connection_indices = []
        for i_src, target_id in connections:
            if target_id not in conn_target_idx_map:
                raise RuntimeError(f'Target ID not found: {target_id}')

            connection_indices.append((i_src, conn_target_idx_map[target_id]))

        return connection_indices


if __name__ == '__main__':
    # Instantiate evaluator from ADORE model, and save generated architectures
    evaluator = GNCFileCMDEvaluator.from_file('../gnc.adore', save_to_project=True)
    assert len(evaluator.objectives) == 2

    # Generate and evaluate some random architectures for testing
    for _ in range(10):
        # Generate architecture for a random design vector
        arch, dv, is_active = evaluator.get_architecture(evaluator.get_random_design_vector())

        # Generate input file
        evaluator.evaluate_get_input(arch, working_dir='outputs')

        # Evaluate the architecture
        obj, con = evaluator.evaluate(arch)
        print(f'DV {dv!r} --> OBJ {obj!r}')
