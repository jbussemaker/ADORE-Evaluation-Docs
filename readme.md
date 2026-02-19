# ADORE Evaluation Docs

This repository documents ADORE's evaluation interfaces.
[ADORE (Architecture Design and Optimization Reasoning Environment)](https://adore.mbse-env.com/)
is a platform to support the implementation of
System Architecture Optimization (SAO) problems.
To do so, it provides an architecture design space modeling GUI, various interfaces for connecting to evaluation
code, and interfaces for connecting to optimization algorithms:

![ADORE Overview](https://adore.mbse-env.com/docs/assets/adore_overview.png)

System Architecture Optimization (SAO) is a subfield of Model-Based Systems Engineering (MBSE) that attempts to
automate part of the system design process by formulating the system architecture design process as a numerical
optimization problem.
The system architecture represents the elements (components) a system consists of, how these fulfill the system
functions, and how they are connected to each other.
In SAO, system architectures are automatically generated in the optimization loop:

![SAO Loop](https://adore.mbse-env.com/docs/assets/opt_loop.png)

ADORE provides the following interfaces to connect to evaluation code:

![Evaluation Interfaces](https://adore.mbse-env.com/docs/assets/interfaces.png)

## Repository Contents

Root folder:
- `ADORE_Evaluation_Interface.pdf`: Documentation of the evaluation interfaces
- `gnc.adore`: GN&C ADORE model
- `gnc_no_act.adore`: GN&C ADORE model, without actuators

### (1) Python API

- `Architecture-DataModel.png`: ADORE `Architecture` data model
- `gnc_evaluation_api[_exercise].py`: Demonstration of / exercise for the Python API

### (2) Python CFE (Class Factory Evaluator)

- `ADORE_Class_Factory_Evaluator_QRM.pdf`: CFE Quick Reference Manual
- `gnc_class_factory_evaluator[_exercise].py`: Demonstration of / exercise for the CFE
- `cfe_examples`: Folder with some additional CFE examples

### (3) File-based Evaluation

- `gnc_file_evaluation[_exercise].py`: Demonstration of / exercise for the file-based evaluation (direct serialization)
- `gnc_file_evaluation_cmd_line.py`: Demonstration of file-based evaluation by starting a separate Python process

### (4) File-based Node Factory Evaluation

- `gnc_node_factory_evaluator_base.xml`: Base file for the GN&C NFE
- `Architecture_1_NFE.xml`: Export of an architecture translated using the NFE
- `nfe_format.xml`: Detailed explanation of the NFE format
- `gnc_node_factory_evaluator[_exercise].py`: Demonstration of / exercise for the NFE

### (4b) CPACS Evaluation

- `cpacs_evaluation_workshop.adore`: ADORE model used for explaining the CPACS factories
- `cpacs_nfe_format.xml`: Detailed explanation of the CPACS factories format
- `cpacs_example_factory.xml`: CPACS example with a component factory defined
- `cpacs_example_reusable_elements.xml`: CPACS example with only reusable elements for defining implicit factories

### (5) Remote File-based Evaluation

- `gnc_adore_opt.py`: Demonstration of the ask-tell interface for remote file-based evaluation
- `adore_rfsao_template.wf`: RCE workflow template for remote file-based evaluation
- `configuration.json`: RCE tool configuration for GN&C NFE
- `gnc_node_factory_evaluation.py`: GN&C NFE script for RCE integration
- `gnc_node_factory_evaluator_base.xml`: Base file for the GN&C NFE
- `gnc_DOE_5.adoreopt`: ADORE Optimization file for a DoE of 5 points
- `gnc_NSGA2_10_5.adoreopt`: ADORE Optimization file for NSGA-II with 5 generations of 10 points
- `rce_integration`: Folder with instructions for how to integrate the AdoreOpt block in RCE
