from dataclasses import dataclass
from adore.optimization.api.factory_evaluator import *
from adore.api.schema import *


@dataclass
class Wing:
    area: float  # m2
    cl: float
    ias: float  # kts

    def calc_lift(self):
        ias_ms = self.ias/1.94384
        rho0 = 1.225  # kg/m3
        return self.cl * .5*rho0*ias_ms**2 * self.area


class WingClassAutoFactoryEvaluator(ClassFactoryApiEvaluator):

    def get_class_factories(self) -> List[ClassFactory]:
        return [
            ClassFactory(
                el=ExternalComponentDef(name='Wing', n_inst=[1], auto_match_pattern='/W.*/'),
                cls=Wing,
                props={
                    'area': ExternalQOIDef(
                        name='Wing Area', qoi_type=QOIType.DESIGN_VAR, bounds=(40., 60.),
                        auto_match_pattern='area', units='m^2'),
                    'cl': ExternalQOIDef(
                        name='Lift Coefficient', qoi_type=QOIType.DESIGN_VAR, bounds=(0., .5),
                        auto_match_pattern=['cl', 'L* Coefficient']),
                    'ias': ExternalQOIDef(
                        name='Indicated Airspeed', qoi_type=QOIType.INPUT_PARAM, value=100.,
                        auto_match_pattern='i?s', units='kts'),
                },
            )
        ]

    def get_metrics_factory(self) -> MetricsFactory:
        return MetricsFactory(metrics={
            'lift': ExternalQOIDef(
                name='Lift', qoi_type=QOIType.CONSTRAINT, ref_value=15000*9.81, pos_better=True, auto=True, units='N'),
        })

    def _evaluate(self, architecture: Architecture, arch_qois: List[ArchQOI], **kwargs) -> Dict[ArchQOI, float]:
        # Instantiate classes: we expect one instance of Wing
        objects = self.instantiate(architecture)
        wing = objects[0]
        assert isinstance(wing, Wing)

        # Perform calculations
        results = {
            'lift': self.quantity(wing.calc_lift(), 'N'),
        }

        # Interpret results so that ADORE can process them
        return self.process_results(architecture, arch_qois, results)


if __name__ == '__main__':
    # 1) Instantiate evaluator
    evaluator = WingClassAutoFactoryEvaluator.from_file('Class_Factory_Evaluator_Unlinked.adore')

    # 2) Auto match elements
    evaluator.update_external_databases()
    evaluator.to_file('auto_linked.adore')

    # 3) Test instantiation and results processing
    classes = evaluator.instantiate(evaluator.project.architectures[0])

    architecture = evaluator.project.architectures[0]
    metric_qois = evaluator.get_arch_metric_qois(architecture)
    output = evaluator.process_results(architecture, metric_qois, {'lift': 10000})

    # 4) Test evaluation
    architecture, dv, is_active = evaluator.get_architecture(evaluator.get_random_design_vector())
    evaluator.evaluate(architecture)

    print('DONE')
