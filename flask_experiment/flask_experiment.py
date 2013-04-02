# -*- coding: utf-8 -*-
"""
flask.ext.experiment
====================


"""

import random
import os
from uuid import uuid4
from jinja2 import BaseLoader
from werkzeug.contrib.securecookie import SecureCookie
from flask import request, helpers


"""
PUBLIC API
"""


class ExperimentMapper(object):
    """
    Inherit from this class and define your peristance methods
    """
    def get_subject_experiments(self, subj_id):
        """
        - subj_id - Unique identifier of test subject

        Returns:
            dict - keys are experiment names, values are the variant name
        """
        pass

    def add_subject_experiment(self, subj_id, exp, var):
        """
        - subj_id - Unique identifier of test subject
        - exp - Experiment object
        - var - Variant object
        """
        pass

    def update_subject_experiments(self, subj_id, set_exp, set_var):
        """
        - subj_id - Unique identifier of test subject
        - exp - Experiment object
        - var - Variant object
        """
        pass

"""
PRIVATE API
"""


class ExperimentJinjaLoader(BaseLoader):
    """
    Template loader which maps to html templates from the correct test folders
    """
    def __init__(self, app, flask_loader):
        self._app = app
        self._flask_loader = flask_loader

    def get_source(self, environment, template):
        if request.exp_enabled:
            #self._app.logger.debug("Getting source {} for experiments {}".format(
                #template, request.experiments))

            # 1) Check the non-control variants this subject is in for the template
            for exp, var in request.experiments.iteritems():
                #self._app.logger.debug("Checking experiment {} {}".format(exp.name, var.name))
                if not var.control:
                    tpl = self.get_variant_template(environment, template, exp, var)

                    if tpl:
                        #self._app.logger.debug("Serving template {} from exp/variant {} {}".format(
                            #template, exp.name, var.name))
                        return tpl
                    #else:
                        #self._app.logger.debug("NOT Serving template {} from exp/variant {} {}".format(
                            #template, exp.name, var.name))
        #else:
            #self._app.logger.debug("Experiments not enabled {}".format(template))

        # 2) Check the control variants this subject is in for the template
        # 3) Just return the default template
        #self._app.logger.debug("Serving default template {}".format(template))
        return self.get_default_template(environment, template)

    def get_variant_template(self, environment, template, exp, var):
        try:
            return self._flask_loader.get_source(environment, os.path.join(exp.name, var.name, template))
        except:
            pass

    def get_default_template(self, environment, template):
        return self._flask_loader.get_source(environment, template)

    def list_templates(self):
        return self._flask_loader.list_templates()


class ExperimentManager(object):
    def __init__(self, mapper):
        self.mapper = mapper
        self.experiments = {}

    def add_experiment(self, experiment):
        self.experiments[experiment.name] = experiment

    def update_subject_experiments(self, subj_id, set_exp, set_var):
        exp = self.experiments[set_exp]
        var = exp.variant_map[set_var]

        self.mapper.update_subject_experiments(subj_id, exp, var)

    def get_subject_experiments(self, subj_id):
        exp_map = self.mapper.get_subject_experiments(subj_id)

        out_exp_map = {}

        for exp_name, exp in self.experiments.iteritems():
            if exp_name in exp_map:
                var_name = exp_map[exp_name]
                var = exp.variant_map[var_name]
            else:
                var = self.assign_variant(subj_id, exp)

            #exp_list.append((exp, var))
            out_exp_map[exp] = var

        return out_exp_map

    def assign_variant(self, subj_id, exp):
        var = exp.choose_variant()

        self.mapper.add_subject_experiment(subj_id, exp, var)

        return var


class Experiment(object):
    def __init__(self, name, enabled, variants, index=None):
        self.name = name
        self.enabled = enabled
        self.variants = variants
        self.variant_map = {v.name: v for v in variants}
        self.index = index

        self.enabled_weight = 0
        for v in variants:
            if v.enabled:
                self.enabled_weight += v.weight

    def choose_variant(self):
        r = random.uniform(0, self.enabled_weight)

        upto = 0
        for var in self.variants:
            if var.enabled:
                if upto + var.weight > r:
                    return var
                upto += var.weight

        assert False, "Shouldn't get here"


class Variant(object):
    def __init__(self, name, enabled=False, control=False, weight=0):
        self.name = name
        self.enabled = enabled
        self.control = control
        self.weight = weight


class FlaskExperiment(object):
    def __init__(self, mgr):
        self.mgr = mgr

    def setup_app(self, app):
        self._app = app

        # 1) Redirect jinja template loading through us
        self._app.jinja_loader = ExperimentJinjaLoader(self._app, self._app.jinja_loader)

        # 2) Set up our before and after request hooks
        self._app.before_request(self.before_request)
        self._app.after_request(self.after_request)

        # 3) Disable caching of templates so we can send a unique template to each subject
        opts = dict(self._app.jinja_options)
        opts['cache_size'] = 0
        self._app.jinja_options = opts

        # 4) Override url_for so that we can redirect statics
        def experiment_url_for(endpoint, **values):
            if endpoint != 'static':
                return helpers.url_for(endpoint, **values)

            if request.exp_enabled:
                for exp, var in request.experiments.iteritems():
                    if not var.control:
                        path = self.url_for_get_variant_static(values['filename'], exp, var)

                        if path:
                            values['filename'] = path
                            break

            return helpers.url_for(endpoint, **values)

        rv = self._app.jinja_env
        rv.globals.update(
            url_for=experiment_url_for
        )

        rv.cache = None

    def before_request(self):
        """
        For a new incoming request ensure an id is set in a cookie which can be used to track
        variants for this test subject.
        """

        self.init_cookie()

    def after_request(self, response):
        """
        After a request we should save the cookie if necessary
        """
        if request.exp_enabled:
            exp_cookie = request.exp_cookie

            if exp_cookie.should_save:
                try:
                    exp_cookie.save_cookie(response)
                except:
                    self._app.logger.exception("Failed saving cookie")

        return response

    def init_cookie(self):
        """
        Ensures that a cookie'd subject id exists
        """

        #self._app.logger.debug("Init cookie hit for {}".format(request.path))

        # Don't bother setting the cookie on favicon hits
        # TODO: Make this more gooder
        if request.path == '/favicon.ico/':
            request.exp_enabled = False
            return

        exp_cookie = SecureCookie.load_cookie(request, secret_key=self._app.secret_key)
        subj_id = exp_cookie.get('id')
        if not subj_id:
            subj_id = uuid4().hex
            exp_cookie['id'] = subj_id

        set_exp = request.args.get('experiment')
        set_var = request.args.get('variant')

        request.exp_cookie = exp_cookie
        request.experiments = self.mgr.get_subject_experiments(subj_id)

        if set_exp and set_var:
            self.mgr.update_subject_experiments(subj_id, set_exp, set_var)
            request.experiments = self.mgr.get_subject_experiments(subj_id)

        #self._app.logger.debug("Subject {} experiments {}".format(
            #subj_id, request.experiments))

        request.exp_enabled = True

    def url_for_get_variant_static(self, path, exp, var):
        """
        Check to see if a variant has a static file overriding the base static file
        """
        full_path = os.path.join(self._app.static_folder, exp.name, var.name, path)

        if os.path.exists(full_path):
            return os.path.join(exp.name, var.name, path)


def in_variant(exp_name, *args):
    """
    Returns true if the current subject is in any of the listed variants for exp_name
    """
    if not request.exp_enabled:
        return False

    for exp, var in request.experiments.iteritems():
        if exp.name == exp_name:
            if var.name in args:
                return True

    return False
