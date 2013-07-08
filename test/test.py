from flask import Flask, render_template
from collections import defaultdict

import sys
sys.path.insert(0, 'flask_experiment')
import flask_experiment


class TestMapper(flask_experiment.ExperimentMapper):
    def __init__(self):
        self.subj_map = defaultdict(dict)

    def get_subject_experiments(self, subj_id):
        """
        - subj_id - Unique identifier of test subject

        Returns:
            dict - keys are experiment names, values are the variant name
        """
        return self.subj_map[subj_id]

    def add_subject_experiment(self, subj_id, exp, var):
        """
        - subj_id - Unique identifier of test subject
        - exp - Experiment object
        - var - Variant object
        """
        print "Adding subject to", exp.name, var.name
        self.subj_map[subj_id][exp.name] = var.name

    def update_subject_experiments(self, subj_id, exp, var):
        """
        - subj_id - Unique identifier of test subject
        - exp - Experiment object
        - var - Variant object
        """
        print "Updating subject to", exp.name, var.name
        self.subj_map[subj_id][exp.name] = var.name


mgr = flask_experiment.ExperimentManager(TestMapper())

exp1_vars = [
    flask_experiment.Variant("var1", enabled=True, control=True, weight=50),
    flask_experiment.Variant("var2", enabled=True, control=False, weight=50)
]

mgr.add_experiment(flask_experiment.Experiment("exp1", True, exp1_vars))

exp2_vars = [
    flask_experiment.Variant("e2_control", enabled=True, control=True, weight=50),
    flask_experiment.Variant("e2_var2", enabled=True, control=False, weight=50)
]

mgr.add_experiment(flask_experiment.Experiment("exp2", True, exp2_vars))

exp3_vars = [
    flask_experiment.Variant("e3_control", enabled=True, control=True, weight=50),
    flask_experiment.Variant("e3_var2", enabled=True, control=False, weight=50)
]

mgr.add_experiment(flask_experiment.Experiment("exp3", True, exp3_vars))

exp4_vars = [
    flask_experiment.Variant("e4_control", enabled=True, control=True, weight=50),
    flask_experiment.Variant("e4_var2", enabled=True, control=False, weight=50)
]

mgr.add_experiment(flask_experiment.Experiment("exp4", True, exp4_vars))


exp = flask_experiment.FlaskExperiment(mgr)
app = Flask(__name__)
app.secret_key = "asdf"

exp.setup_app(app)


@app.route('/')
def hello_world():
    print "Exp 1Var1", flask_experiment.in_variant("exp1", "var1")
    print "Exp 1Var2", flask_experiment.in_variant("exp1", "var2")
    print "Exp1 Either", flask_experiment.in_variant("exp1", "var1", "var2")

    return render_template("exp2/exp2.html")

if __name__ == '__main__':
    app.run(debug=True)
