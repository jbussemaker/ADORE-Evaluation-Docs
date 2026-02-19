import os
import json
import shutil
import tempfile
from typing import Tuple
from gnc import GNCCalculator
from adore.optimization.bridge.cli import tell_ask
from adore.optimization.bridge.manager import OptimizationManager
from adore.optimization.api.file_based.direct_file_evaluators import JSONFileEvaluator
from adore.api.schema import *


class GNCFileEvaluator(JSONFileEvaluator):
    """
    Evaluate the GN&C architecture defined in the gnc.adore (or gnc_no_act.adore) model, using file-based evaluation.
    Here, we emulate an external evaluation process, however implement the file evaluation in this same Python file.
    """

    def _evaluate_file(self, input_file_path: str, output_file_path: str):
        self.gnc_json_evaluate(input_file_path, output_file_path)

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
    OptimizationManager.capture_log()

    # Copy the initial adoreopt file
    adoreopt_file = 'outputs/gnc.adoreopt'
    shutil.copy('gnc_NSGA2_10_5.adoreopt', adoreopt_file)

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_file = f'{tmp_dir}/input.json'
        output_file = f'{tmp_dir}/output.json'

        # Run the tell-ask loop
        while True:
            # Tell results if available, and ask for a new architecture if available
            tell_ask(adoreopt_file, adoreopt_file, output_file, input_file)

            # If no new input file has been created, there are no more architectures to evaluate and we can quit
            if not os.path.exists(input_file):
                break

            # Evaluate the architecture
            # NOTE: this step can be done in an external execution environment
            GNCFileEvaluator.gnc_json_evaluate(input_file, output_file)
            assert os.path.exists(output_file)

    # Output results
    manager = OptimizationManager.from_file(adoreopt_file)
    evaluator = manager.eval_factory.evaluator
    evaluator.to_file('outputs/gnc_ask_tell.adore')
    evaluator.save_results_csv('outputs/gnc_ask_tell_file_evaluation.csv')
    GNCCalculator.plot_results(evaluator.get_results(), 'JSON Ask-Tell File Evaluator')
