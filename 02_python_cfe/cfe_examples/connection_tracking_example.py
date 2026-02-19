from dataclasses import dataclass
from adore.optimization.api.factory_evaluator import *
from adore.api.schema import *


@dataclass
class ConnObj:
    arch_el: ArchElement
    all: list
    inputs: list
    outputs: list


class ConnectionExampleEvaluator(ClassFactoryApiEvaluator):

    def get_class_factories(self) -> List[ClassFactory]:
        # External element definitions (to connect to architecture design space elements)
        func_def = ExternalFunctionDef('Function', auto_match_pattern='Function*')
        comp_def = ExternalComponentDef('Component', auto_match_pattern='Component*')
        concept_def = ExternalElementDef('Concept', el_types=[Concept], auto=True)
        de_def = ExternalElementDef('Decomposition', el_types=[Decomposition], auto=True)
        nf_def = ExternalElementDef('Non-fulfillment', el_types=[NonFulfillment], auto=True)
        mf_def = ExternalElementDef('Multi-fulfillment', el_types=[MultiFulfillment], auto=True)

        # Define class factories: all instantiate the ConnObj, with inputs and outputs tracked
        all_defs = [func_def, comp_def, concept_def, de_def, nf_def, mf_def]
        return [
            ClassFactory(el=func_def, cls=ConnObj, props={
                'arch_el': SpecialValue.El,
                'all': ConnectionValue(conn_target_def=all_defs),
                'inputs': ConnectionValue(conn_target_def=all_defs, input_conn=True),
                'outputs': ConnectionValue(conn_target_def=all_defs, input_conn=False),
            }),
            ClassFactory(el=comp_def, cls=ConnObj, props={
                'arch_el': SpecialValue.El,
                'all': ConnectionValue(conn_target_def=all_defs),
                'inputs': ConnectionValue(conn_target_def=all_defs, input_conn=True),
                'outputs': ConnectionValue(conn_target_def=all_defs, input_conn=False),
            }),
            ClassFactory(el=concept_def, cls=ConnObj, props={
                'arch_el': SpecialValue.El,
                'all': ConnectionValue(conn_target_def=all_defs),
                'inputs': ConnectionValue(conn_target_def=all_defs, input_conn=True),
                'outputs': ConnectionValue(conn_target_def=all_defs, input_conn=False),
            }),
            ClassFactory(el=de_def, cls=ConnObj, props={
                'arch_el': SpecialValue.El,
                'all': ConnectionValue(conn_target_def=all_defs),
                'inputs': ConnectionValue(conn_target_def=all_defs, input_conn=True),
                'outputs': ConnectionValue(conn_target_def=all_defs, input_conn=False),
            }),
            ClassFactory(el=nf_def, cls=ConnObj, props={
                'arch_el': SpecialValue.El,
                'all': ConnectionValue(conn_target_def=all_defs),
                'inputs': ConnectionValue(conn_target_def=all_defs, input_conn=True),
                'outputs': ConnectionValue(conn_target_def=all_defs, input_conn=False),
            }),
            ClassFactory(el=mf_def, cls=ConnObj, props={
                'arch_el': SpecialValue.El,
                'all': ConnectionValue(conn_target_def=all_defs),
                'inputs': ConnectionValue(conn_target_def=all_defs, input_conn=True),
                'outputs': ConnectionValue(conn_target_def=all_defs, input_conn=False),
            }),
        ]

    def _evaluate(self, architecture: Architecture, arch_qois: List[ArchQOI], **kwargs) -> Dict[ArchQOI, float]:
        # conn_obj: List[ConnObj] = self.instantiate(architecture)
        # assert len(conn_obj) == 12

        func_conn_objs: List[ConnObj] = self.instantiate(
            architecture, factories=self.get_factories_by_el_name('Function'))
        assert len(func_conn_objs) == 5

        comp_conn_objs: List[ConnObj] = self.instantiate(
            architecture, factories=self.get_factories_by_el_name('Component'))
        assert len(comp_conn_objs) == 3

        multi_fulfill_con_objs: List[ConnObj] = self.instantiate(
            architecture, factories=self.get_factories_by_el_name('Multi-fulfillment'))
        assert len(multi_fulfill_con_objs) == 1

        # Component 1 (instance 1) connections:
        # Inputs from Function 3 and Multi-fulfillment
        assert comp_conn_objs[0].inputs == [func_conn_objs[2], multi_fulfill_con_objs[0]]
        # Output to Function 5
        assert comp_conn_objs[0].outputs == [func_conn_objs[4]]

        # Component 1 (instance 2) has the same connections
        assert comp_conn_objs[1].inputs == [func_conn_objs[2], multi_fulfill_con_objs[0]]
        assert comp_conn_objs[1].outputs == [func_conn_objs[4]]

        # Component 2 is only connect to Multi-fulfillment (input)
        assert comp_conn_objs[2].inputs == [multi_fulfill_con_objs[0]]
        assert comp_conn_objs[2].outputs == []

        print('ALL CONNECTIONS OK!')
        return self.process_results(architecture, arch_qois, {})

    def get_metrics_factory(self) -> MetricsFactory:
        return MetricsFactory(metrics={})


if __name__ == '__main__':
    evaluator = ConnectionExampleEvaluator.from_file('Connection_Tracking_Example.adore')
    evaluator.update_external_databases()
    evaluator.evaluate(evaluator.project.architectures[0])
