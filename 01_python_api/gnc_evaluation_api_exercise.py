import adore as ad
from typing import List, Dict, Tuple
from gnc import GNCCalculator


class GNCEvaluator(ad.GraphApiEvaluator):
    """
    Evaluate the GN&C architecture defined in the gnc.adore (or gnc_no_act.adore) model, using the Evaluation API.
    This is the lowest-level API access available, and involves directly parsing the Architecture instance provided
    as input.
    """

    def _evaluate(self, architecture: ad.Architecture, arch_qois: List[ad.ArchQOI], **_) -> Dict[ad.ArchQOI, float]:
        # Get element types
        sensor_types = self._get_element_types(architecture, 'sensor')
        computer_types = self._get_element_types(architecture, 'computer')
        actuator_types = self._get_element_types(architecture, 'actuator')
        if len(actuator_types) == 0:  # Check if this model includes actuators
            actuator_types = None

        # Get element connections
        sensor_computer_conns = self._get_element_connections(architecture, 'sensor', 'computer')
        computer_actuator_conns = None
        if actuator_types is not None:
            computer_actuator_conns = self._get_element_connections(architecture, 'computer', 'actuator')

        # Calculate metrics
        arch_qoi_map = {}
        for arch_qoi in arch_qois:
            if arch_qoi.ref == 'mass':
                mass = GNCCalculator.calc_mass(sensor_types, computer_types, actuator_types)
                arch_qoi_map[arch_qoi] = self.quantity(mass, 'kg')
            elif arch_qoi.ref == 'failure-rate':
                arch_qoi_map[arch_qoi] = GNCCalculator.calc_failure_rate(
                    sensor_types, computer_types, sensor_computer_conns, actuator_types, computer_actuator_conns)
        return arch_qoi_map

    @staticmethod
    def _get_element_types(architecture: ad.Architecture, element_ref: str) -> List[str]:
        """Parses the Architecture to find the amount and types of the provided element, matching by name"""

        types = []

        # TODO implement code here:
        #  - Loop over system components
        #  - Match components by ref
        #  - For each component, loop over instances
        #  - For each instance, get the type attribute value (and add to the list)

        return types

    @staticmethod
    def _get_element_connections(architecture: ad.Architecture, src_ref: str, tgt_ref: str) -> List[Tuple[int, int]]:
        """Parses the Architecture to find port connections between two types of elements"""

        # First find all outgoing connections from source elements, and available connection targets
        connections = []
        conn_target_idx_map = {}
        for component in architecture.system.components:
            # Match by source element
            if component.ref == src_ref:
                # Loop over component instances
                for instance in component.instances:
                    # Loop over outgoing port connections
                    for out_port_connection in instance.output_ports:
                        # Loop over target connections
                        for target_id in out_port_connection.target_ids:
                            connections.append((instance.index, target_id))

            # Match by target element
            elif component.ref == tgt_ref:
                # Get available connection targets
                for instance in component.instances:
                    for in_port_connection in instance.input_ports:
                        conn_target_idx_map[in_port_connection.id] = instance.index

        # Convert connection target IDs to instance indices
        connection_indices = []
        for i_src, target_id in connections:
            if target_id not in conn_target_idx_map:
                raise RuntimeError(f'Target ID not found: {target_id}')

            connection_indices.append((i_src, conn_target_idx_map[target_id]))

        return connection_indices


if __name__ == '__main__':
    # Instantiate evaluator from ADORE model, and save generated architectures
    evaluator = GNCEvaluator.from_file('../gnc.adore', save_to_project=True)
    assert len(evaluator.objectives) == 2

    # Generate and evaluate some random architectures for testing
    for _ in range(10):
        # Generate architecture for a random design vector
        arch, dv, is_active = evaluator.get_architecture(evaluator.get_random_design_vector())

        # Evaluate the architecture
        obj, con = evaluator.evaluate(arch)
        print(f'DV {dv!r} --> OBJ {obj!r}')

    # Connect to SBArchOpt/pymoo for optimization
    from sb_arch_opt.algo.pymoo_interface import get_nsga2
    from pymoo.optimize import minimize

    problem = evaluator.get_arch_opt_problem()
    algorithm = get_nsga2(pop_size=50)  # Normally, you'd also add a `results_folder` here!
    result = minimize(problem, algorithm, termination=('n_gen', 10), verbose=True)
    assert len(result.opt) > 1  # Check that we indeed have a Pareto front

    # Save ADORE evaluator results
    evaluator.to_file('outputs/gnc_evaluation_api.adore')
    evaluator.save_results_csv('outputs/gnc_evaluation_api.csv')
    GNCCalculator.plot_results(evaluator.get_results(), 'Evaluation API')
