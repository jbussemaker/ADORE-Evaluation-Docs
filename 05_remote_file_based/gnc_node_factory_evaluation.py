from lxml import etree
from gnc import GNCCalculator


class GNCNodeFactoryEvaluator:
    """
    Evaluate the GN&C architecture defined in the gnc.adore (or gnc_no_act.adore) model, using XML node factory
    evaluation. Here, we emulate an external evaluation process, however implement the file evaluation in this same
    Python file.
    """

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
    def _get_element_types(tree: etree._ElementTree, xpath):

        # Loop over all element nodes
        types = []
        for obj_el in tree.xpath(xpath):
            # Get value of type node
            obj_type = obj_el.find('type').text
            assert obj_type in ['A', 'B', 'C']
            types.append(obj_type)

        return types

    @staticmethod
    def _get_element_connections(tree: etree._ElementTree, src_xpath: str, tgt_xpath: str):

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
    import argparse
    parser = argparse.ArgumentParser('GNC XML NFE evaluator')
    parser.add_argument('input_file')
    parser.add_argument('output_file')
    args = parser.parse_args()

    GNCNodeFactoryEvaluator.gnc_xml_nfe_evaluate(args.input_file, args.output_file)
