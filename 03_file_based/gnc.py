import argparse
import itertools
import numpy as np
import pandas as pd


class GNCCalculator:
    """
    Modeled after the Guidance, Navigation & Control problem of:
    Crawley et al., "System Architecture - Strategy and Product Development for Complex Systems", 2015.
    Apaza & Selva, "Automatic Composition of Encoding Scheme and Search Operators in System Architecture Optimization", 2021.

    The problem is as follows: find the Pareto front of optimal GN&C architectures, trading-off system mass (as a proxy
    for cost) and failure probability. The architecture consists of multiple sensors, connected to multiple
    flight computers, connected to multiple actuators. Each element is connected to at least one other element.
    For each element there are three options available (A, B and C), each with different mass and failure probability.
    Optionally, the number of elements (each element separately) is a choice as well.

    Optionally, only sensors and computers are modeled to reduce the size of the design space.
    """

    # Mass and failure rate properties for sensors, computers, and actuators
    mass = {
        'S': {'A': 3., 'B': 6., 'C': 9.},
        'C': {'A': 3., 'B': 5., 'C': 10.},
        'A': {'A': 3.5, 'B': 5.5, 'C': 9.5},
    }
    failure_rate = {
        'S': {'A': .00015, 'B': .0001, 'C': .00005},
        'C': {'A': .0001, 'B': .00004, 'C': .00002},
        'A': {'A': .00008, 'B': .0002, 'C': .0001},
    }

    @classmethod
    def calc_mass(cls, sensor_types, computer_types, actuator_types=None):
        """Calculate system mass by summation of component masses"""
        mass = sum([cls.mass['S'][type_] for type_ in sensor_types])
        mass += sum([cls.mass['C'][type_] for type_ in computer_types])
        if actuator_types is not None:
            mass += sum([cls.mass['A'][type_] for type_ in actuator_types])
        return mass

    @classmethod
    def calc_failure_rate(cls, sensor_types, computer_types, conns, actuator_types=None, act_conns=None):
        """
        Calculate log_10 of failure rate by considering all possible failure cases:
        - Failure of all elements at some stage (sensors, computers, actuators)
        - Failure of one or more elements at some stage and all remaining downstream connected elements
        - Failure of downstream elements

        Connections should be given in a list of tuples with indices (e.g. [(0, 1), (1, 2), (1, 0), ...]).
        Actuator connections/failures are optional.
        """

        # Get item failure rates
        rate = cls.failure_rate
        failure_rates = [np.array([rate['S'][type_] for type_ in sensor_types]),
                         np.array([rate['C'][type_] for type_ in computer_types])]
        obj_conns = [conns]
        if actuator_types is not None:
            failure_rates.append(np.array([rate['A'][type_] for type_ in actuator_types]))
            obj_conns.append(act_conns)

        # Construct connection matrices to determine remaining connections in case of failure
        conn_matrices = []
        for i, edges in enumerate(obj_conns):
            matrix = np.zeros((len(failure_rates[i]), len(failure_rates[i+1])), dtype=int)
            for i_src, i_tgt in edges:
                matrix[i_src, i_tgt] = 1
            conn_matrices.append(matrix)

        # Loop over combinations of failed components
        def _branch_failures(i_rates=0, src_connected_mask=None) -> float:
            calc_downstream = i_rates < len(conn_matrices)-1
            rates, tgt_rates = failure_rates[i_rates], failure_rates[i_rates+1]
            conn_mat = conn_matrices[i_rates]

            # Loop over failure scenarios
            if src_connected_mask is None:
                src_connected_mask = np.ones((len(rates),), dtype=bool)
            total_rate = 0.
            for ok_sources in itertools.product(*[([False, True] if src_connected_mask[i_conn] else [False])
                                                  for i_conn in range(len(rates))]):
                # The scenario of all remaining computers has already been considered
                if i_rates > 0 and not any(ok_sources):
                    continue

                # Calculate probability of this scenario occurring
                ok_sources = list(ok_sources)
                occurrence_prob = rates.copy()
                occurrence_prob[ok_sources] = 1-occurrence_prob[ok_sources]
                prob = 1.
                for partial_prob in occurrence_prob[src_connected_mask]:
                    prob *= partial_prob
                occurrence_prob = prob

                # Check which targets are still connected in this scenario
                conn_mat_ok = conn_mat[ok_sources, :].T
                connected_targets = np.zeros((conn_mat_ok.shape[0],), dtype=bool)
                for i_conn_tgt in range(conn_mat_ok.shape[0]):
                    connected_targets[i_conn_tgt] = np.any(conn_mat_ok[i_conn_tgt])

                # If no connected targets are available the system fails
                tgt_failure_rates = tgt_rates[connected_targets]
                if len(tgt_failure_rates) == 0:
                    total_rate += occurrence_prob
                    continue

                # Calculate the probability that the system fails because all remaining connected targets fail
                all_tgt_fail_prob = 1.
                for prob in tgt_failure_rates:
                    all_tgt_fail_prob *= prob
                total_rate += occurrence_prob*all_tgt_fail_prob

                # Calculate the probability that the system fails because remaining downstream connected targets fail
                if calc_downstream:
                    total_rate += occurrence_prob*_branch_failures(
                        i_rates=i_rates+1, src_connected_mask=connected_targets)

            return total_rate

        failure_rate = _branch_failures()
        return np.log10(failure_rate)

    @staticmethod
    def plot_results(results_df: pd.DataFrame, evaluator_name: str):
        import matplotlib.pyplot as plt
        obj_cols = [col for col in results_df.columns if col.startswith('OBJ_')]
        pareto_df = results_df.where(results_df.inParetoFront)

        plt.figure(), plt.title(f'GN&C Problem Results: {evaluator_name}')
        plt.scatter(results_df[obj_cols[0]], results_df[obj_cols[1]], s=5, c='k', label='Architectures')
        plt.scatter(pareto_df[obj_cols[0]], pareto_df[obj_cols[1]], s=20, c='b', label='Pareto front')
        plt.xlabel('System Failure Rate (log_10)'), plt.ylabel('System Mass [kg]')
        plt.legend()
        plt.show()


def cli():
    parser = argparse.ArgumentParser('GNC JSON Evaluator')

    parser.add_argument('input', type=str, help='Path to input JSON file')
    parser.add_argument('output', type=str, help='Desired output JSON file path')

    args = parser.parse_args()

    from gnc_file_evaluation_cmd_line import GNCFileCMDEvaluator
    print(f'Processing input: {args.input}')
    GNCFileCMDEvaluator.gnc_json_evaluate(args.input, args.output)
    print(f'Written output to: {args.output}')


if __name__ == '__main__':
    cli()
