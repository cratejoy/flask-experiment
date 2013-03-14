# Flask-Experiment

__Multivariate Experiment Extension for Flask__

Makes serving different templates and static files for the purposes of running multivariate experiments very easy.

1. Set up directory structure
```
./templates/index.html
./templates/experiment1
./templates/experiment1/variant2/index.html
```

2. import flask_experiment


3. Inherit from TestMapper and persist subject id to experiment to variant mappings. The following simply saves them to a dictionary in memory (subj_map)
```python
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
```

4. Create an experiment manager
```python
mgr = flask_experiment.ExperimentManager(TestMapper())
```

5. Define your experiments
```python
exp1_vars = [
    flask_experiment.Variant("var1", enabled=True, control=True, weight=50),
    flask_experiment.Variant("var2", enabled=True, control=False, weight=50)
]
mgr.add_experiment(flask_experiment.Experiment("exp1", True, exp1_vars))
```

6. Create a flask experiment instance and initialize the flask app
```python
exp = flask_experiment.FlaskExperiment(mgr)
app = Flask(__name__)
app.secret_key = "asdf"
exp.setup_app(app)
```
