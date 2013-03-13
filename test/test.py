from flask import Flask, render_template
from collections import defaultdict

import sys
sys.path.insert(0, 'flask-experiment')
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


mgr = flask_experiment.ExperimentManager(TestMapper())

exp1_vars = [
    flask_experiment.Variant("var1", enabled=True, control=True, weight=50),
    flask_experiment.Variant("var2", enabled=True, control=False, weight=50)
]

mgr.add_experiment(flask_experiment.Experiment("exp1", True, exp1_vars))


exp = flask_experiment.FlaskExperiment(mgr)
app = Flask(__name__)
app.secret_key = "asdf"

exp.setup_app(app)


@app.route('/')
def hello_world():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
