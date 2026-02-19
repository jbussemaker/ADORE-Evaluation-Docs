from dataclasses import dataclass
from adore.optimization.api.factory_evaluator import *
from adore.api.schema import *


@dataclass
class PortObj:
    name: str


@dataclass
class SourceObj:
    targets: List['TargetObj']
    target_ports: List[PortObj]


@dataclass
class TargetObj:
    sources: List[SourceObj]
    source_ports: List[PortObj]


class PortExampleEvaluator(ClassFactoryApiEvaluator):

    def get_class_factories(self) -> List[ClassFactory]:
        port_def = ExternalPortDef(name='ExtPort')
        return [
            ClassFactory(
                el=port_def, cls=PortObj, props={
                    'name': SpecialValue.Name,
                },
            ),
            ClassFactory(
                el=ExternalComponentDef(name='Source'), cls=SourceObj,
                props={
                    'targets': ConnectionValue(conn_target_def=port_def, input_conn=False),
                    'target_ports': ConnectionValue(conn_target_def=port_def, return_ports=True),
                },
            ),
            ClassFactory(
                el=ExternalComponentDef(name='Target'), cls=TargetObj,
                props={
                    'sources': ConnectionValue(conn_target_def=port_def, input_conn=True),
                    'source_ports': ConnectionValue(conn_target_def=port_def, return_ports=True),
                },
            ),
        ]

    def _evaluate(self, architecture: Architecture, arch_qois: List[ArchQOI], **kwargs) -> Dict[ArchQOI, float]:
        port_objs = self.instantiate(architecture, factories=self.get_factories_by_el_name('ExtPort'))
        src_objs = self.instantiate(architecture, factories=self.get_factories_by_el_name('Source'))
        tgt_objs = self.instantiate(architecture, factories=self.get_factories_by_el_name('Target'))

        assert isinstance(src_objs[0], SourceObj)
        assert src_objs[0].target_ports == [port_objs[0]]
        assert src_objs[0].targets == [tgt_objs[0]]

        assert isinstance(tgt_objs[0], TargetObj)
        assert tgt_objs[0].source_ports == [port_objs[0]]
        assert tgt_objs[0].sources == [src_objs[0]]

        return self.process_results(architecture, arch_qois, {})

    def get_metrics_factory(self) -> MetricsFactory:
        return MetricsFactory(metrics={})


if __name__ == '__main__':
    # PortExampleEvaluator.export_external_database('ports'+PortExampleEvaluator.FILE_EXT)

    evaluator = PortExampleEvaluator.from_file('Port_Example.adore')
    evaluator.evaluate(evaluator.project.architectures[0])
