from lxml import etree
from typing import Tuple
from adore.optimization.api.file_based.file_factory_evaluator import XMLNodeFactoryEvaluator
from adore.api.schema import *
from gnc import GNCCalculator


class GNCNodeFactoryEvaluator(XMLNodeFactoryEvaluator):
    """
    Evaluate the GN&C architecture defined in the gnc.adore (or gnc_no_act.adore) model, using XML node factory
    evaluation. Here, we emulate an external evaluation process, however implement the file evaluation in this same
    Python file.

    The following XML format is used:
    ```
    <gnc>
        <sensors>
            <sensor>
                <type>B</type><!-- A, B, C -->
                <targets>Computer_0_33aa80</targets><!-- Linked by uID -->
            </sensor>
            ...
        </sensors>
        <computers>
            <computer uID="Computer_0_33aa80">
                <type>B</type>
                <targets>Actuator_0_165534</targets>
            </computer>
            ...
        </computers>
        <actuators>
            <actuator uID="Actuator_0_165534">
                <type>A</type>
            </actuator>
            ...
        </actuators>
        <performance>
            <mass>100</mass>
            <failureRate>.5</failureRate>
        </performance>
    </gnc>
    ```
    """

    def _evaluate_file(self, input_file_path: str, output_file_path: str):
        self.gnc_xml_nfe_evaluate(input_file_path, output_file_path)

    @classmethod
    def gnc_xml_nfe_evaluate(cls, input_file: str, output_file: str):
        """Class method to show that the file evaluation process does not need anything in the instantiated evaluator"""

        # Load XML file
        tree = etree.parse(input_file)

        # Get element types
        sensor_types = cls._get_element_types(tree, '/gnc/sensors/sensor')
        computer_types = cls._get_element_types(tree, '/gnc/computers/computer')
        actuator_types = cls._get_element_types(tree, '/gnc/actuators/actuator')
        if len(actuator_types) == 0:  # Check if this model includes actuators
            actuator_types = None

        # Get element connections
        sensor_computer_conns = cls._get_element_connections(tree, '/gnc/sensors/sensor', '/gnc/computers/computer')
        computer_actuator_conns = None
        if actuator_types is not None:
            computer_actuator_conns = cls._get_element_connections(tree, '/gnc/computers/computer', '/gnc/actuators/actuator')

        # Calculate and output metrics
        mass = GNCCalculator.calc_mass(sensor_types, computer_types, actuator_types)
        mass_el = tree.xpath('/gnc/performance/mass')[0]
        mass_el.text = str(mass)
        mass_el.attrib['units'] = 'kg'

        failure_rate = GNCCalculator.calc_failure_rate(
            sensor_types, computer_types, sensor_computer_conns, actuator_types, computer_actuator_conns)
        fr_el = tree.xpath('/gnc/performance/failureRate')[0]
        fr_el.text = str(failure_rate)

        # Write output file
        with open(output_file, 'wb') as fp:
            fp.write(etree.tostring(tree, encoding='utf-8', pretty_print=True))

    @staticmethod
    def _get_element_types(tree: etree._ElementTree, xpath) -> List[str]:

        # Loop over all element nodes
        types = []
        for obj_el in tree.xpath(xpath):
            # Get value of type node
            obj_type = obj_el.find('type').text
            assert obj_type in ['A', 'B', 'C']
            types.append(obj_type)

        return types

    @staticmethod
    def _get_element_connections(tree: etree._ElementTree, src_xpath: str, tgt_xpath: str) -> List[Tuple[int, int]]:

        # Get target element uids
        tgt_uid_map = {}
        for i, tgt_el in enumerate(tree.xpath(tgt_xpath)):
            obj_uid = tgt_el.attrib['uID']
            tgt_uid_map[obj_uid] = i

        # Get connection indices
        connections = []
        for i, src_el in enumerate(tree.xpath(src_xpath)):
            target_uids = src_el.find('targets').text.split(',')
            for tgt_uid in target_uids:
                connections.append((i, tgt_uid_map[tgt_uid]))

        return connections


if __name__ == '__main__':
    # Instantiate evaluator from ADORE model, and save generated architectures
    evaluator = GNCNodeFactoryEvaluator.from_file('../gnc.adore', save_to_project=True)
    assert len(evaluator.objectives) == 2

    # Set base file and define where the NFE settings can be found
    evaluator.base_file = 'gnc_node_factory_evaluator_base.xml'
    evaluator.settings_path = '/gnc/adore'

    # Generate and evaluate some random architectures for testing
    for _ in range(10):
        # Generate architecture for a random design vector
        arch, dv, is_active = evaluator.get_architecture(evaluator.get_random_design_vector())

        # Generate input file
        evaluator.evaluate_get_input(arch, working_dir='outputs')

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
    evaluator.to_file('outputs/gnc_node_factory_evaluation.adore')
    evaluator.save_results_csv('outputs/gnc_node_factory_evaluation.csv')
    GNCCalculator.plot_results(evaluator.get_results(), 'XML Node Factory Evaluator')
