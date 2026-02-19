import adore as ad
from typing import List, Dict
from dataclasses import dataclass
from gnc import GNCCalculator


@dataclass
class Sensor:
    type: str
    element: ad.ArchElement
    targets: List['Computer']


@dataclass
class Computer:
    type: str
    element: ad.ArchElement
    targets: List['Actuator']


@dataclass
class Actuator:
    type: str
    element: ad.ArchElement


@dataclass
class Port:
    pass


class GNCClassFactoryEvaluator(ad.ClassFactoryApiEvaluator):
    """
    Evaluate the GN&C architecture defined in the gnc.adore (or gnc_no_act.adore) model,
    using the Class Factory Evaluation API.
    """

    def get_class_factories(self) -> List[ad.ClassFactory]:
        # Define an external element for the type attribute (auto matched by name)
        type_attr = ad.ExternalAttributeDef(name='type', auto=True)

        # Define an external element for the ports
        port_def = ad.ExternalPortDef(name='Ports', auto_match_pattern='*')

        return [
            ad.ClassFactory(  # Class factory for the Sensor (auto matched by name)
                el=ad.ExternalComponentDef(name='sensor', auto=True),
                cls=Sensor,
                props={
                    'type': type_attr,  # Set the type property to the linked attribute value
                    'element': ad.SpecialValue.El,  # Architecture element to track the instance index
                    'targets': ad.ConnectionValue(conn_target_def=port_def, input_conn=False),  # Port connection targets
                },
            ),
            ad.ClassFactory(  # Class factory for the Computer (auto matched by pattern)
                el=ad.ExternalComponentDef(name='computer', auto_match_pattern='comp*'),
                cls=Computer,
                props={
                    'type': type_attr,  # Set the type property to the linked attribute value
                    'element': ad.SpecialValue.El,  # Architecture element to track the instance index
                    'targets': ad.ConnectionValue(conn_target_def=port_def, input_conn=False),  # Port connection targets
                },
            ),

            # TODO add class factory for the actuator (note: no need for tracking connection targets)

            ad.ClassFactory(el=port_def, cls=Port),  # Class factory for linking to all the ports
        ]

    def get_metrics_factory(self) -> ad.MetricsFactory:
        return ad.MetricsFactory(metrics={
            'mass': ad.ExternalQOIDef(name='mass', auto=True, units='kg'),
            'failure_rate': ad.ExternalQOIDef(name='failure-rate', auto=True),
        })

    def _evaluate(self, architecture: ad.Architecture, arch_qois: List[ad.ArchQOI], **kwargs) -> Dict[ad.ArchQOI, float]:

        sensors = []
        computers = []
        actuators = []
        # TODO add code above to instantiate sensor, computer, and actuator classes:
        #  - Use the self.instantiate function
        #  - Use the factories argument to only instantiate specific classes

        if len(actuators) == 0:
            actuators = None

        # Get element types (note: attribute value is a list)
        sensor_types = [sensor.type[0] for sensor in sensors]
        computer_types = [computer.type[0] for computer in computers]
        actuator_types = [actuator.type[0] for actuator in actuators] if actuators is not None else None

        # Get element connections
        sensor_computer_conns = []
        for sensor in sensors:
            assert isinstance(sensor.element, ad.ArchComponentInstance)
            for computer in sensor.targets:
                assert isinstance(computer.element, ad.ArchComponentInstance)
                sensor_computer_conns.append((sensor.element.index, computer.element.index))

        computer_actuator_conns = None
        if actuators is not None:
            computer_actuator_conns = []
            for computer in computers:
                assert isinstance(computer.element, ad.ArchComponentInstance)
                for actuator in computer.targets:
                    assert isinstance(actuator.element, ad.ArchComponentInstance)
                    computer_actuator_conns.append((computer.element.index, actuator.element.index))

        # Calculate and match metrics
        metrics = {
            'mass': GNCCalculator.calc_mass(sensor_types, computer_types, actuator_types),
            'failure_rate': GNCCalculator.calc_failure_rate(
                sensor_types, computer_types, sensor_computer_conns, actuator_types, computer_actuator_conns),
        }

        # TODO add a return statement using the self.process_results function to match metrics to QOIs


if __name__ == '__main__':
    # Instantiate evaluator from ADORE model, and save generated architectures
    evaluator = GNCClassFactoryEvaluator.from_file('../gnc.adore', save_to_project=True)
    assert len(evaluator.objectives) == 2

    # Connect external elements in class and metric factories to model elements
    evaluator.update_external_databases()
    evaluator.to_file('outputs/gnc_cfe_linked.adore')
    exit()  # TODO comment line to continue with the code below

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
    evaluator.to_file('outputs/gnc_class_factory_evaluator.adore')
    evaluator.save_results_csv('outputs/gnc_class_factory_evaluator.csv')
    GNCCalculator.plot_results(evaluator.get_results(), 'Class Factory Evaluator')
