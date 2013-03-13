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
from flask import request


class ExperimentJinjaLoader(BaseLoader):
    def __init__(self, flask_loader):
        self._flask_loader = flask_loader

    def get_source(self, environment, template):
        if request.exp_enabled:
            print "Template getting source", request.path, request.experiments

            # 1) Check the non-control variants this subject is in for the template
            for exp, var in request.experiments:
                if not var.control:
                    print "Getting non control variant", exp, var
                    tpl = self.get_variant_template(environment, template, exp, var)

                    if tpl:
                        return tpl

            # 2) Check the control variants this subject is in for the template
            for exp, var in request.experiments:
                if var.control:
                    print "Getting control variant", exp, var
                    tpl = self.get_variant_template(environment, template, exp, var)

                    if tpl:
                        return tpl

        # 3) Just return the default template
        return self.get_default_template(environment, template)

    def get_variant_template(self, environment, template, exp, var):
        try:
            return self._flask_loader.get_source(environment, os.path.join(exp.name, var.name, template))
        except:
            pass

    def get_default_template(self, environment, template):
        return self._flask_loader.get_source(environment, template)

    def list_templates(self):
        print "Listing templates"
        return self._flask_loader.list_templates()


class ExperimentMapper(object):
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


class ExperimentManager(object):
    def __init__(self, mapper):
        self.mapper = mapper
        self.experiments = {}

    def add_experiment(self, experiment):
        self.experiments[experiment.name] = experiment

    def get_subject_experiments(self, subj_id):
        exp_map = self.mapper.get_subject_experiments(subj_id)
        print "Mapper result", exp_map

        exp_list = []

        for exp_name, exp in self.experiments.iteritems():
            if exp_name in exp_map:
                var_name = exp_map[exp_name]
                print "Subject already mapped", exp_name, var_name
                var = exp.variant_map[var_name]
            else:
                var = self.assign_variant(subj_id, exp)

            exp_list.append((exp, var))

        return exp_list

    def assign_variant(self, subj_id, exp):
        print "Choosing a variant for", subj_id, "experiment", exp.name
        print "Total weight", exp.enabled_weight

        var = exp.choose_variant()

        print "Chose variant", var.name

        self.mapper.add_subject_experiment(subj_id, exp, var)

        return var


class Experiment(object):
    def __init__(self, name, enabled, variants):
        self.name = name
        self.enabled = enabled
        self.variants = variants
        self.variant_map = {v.name: v for v in variants}

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

    def is_enabled(self):
        return self.enabled


class Variant(object):
    def __init__(self, name, enabled=False, control=False, weight=0):
        self.name = name
        self.enabled = enabled
        self.control = control
        self.weight = weight

    def is_enabled(self):
        return self.enabled

    def get_weight(self):
        return self.weight


class FlaskExperiment(object):
    def __init__(self, mgr):
        self.mgr = mgr

    def setup_app(self, app):
        print "Setting up app"

        self._app = app

        self._app.jinja_loader = ExperimentJinjaLoader(self._app.jinja_loader)

        self._app.before_request(self.before_request)
        self._app.after_request(self.after_request)


        opts = dict(self._app.jinja_options)
        opts['cache_size'] = 0

        self._app.jinja_options = opts

    def before_request(self):
        """
        For a new incoming request ensure an id is set in a cookie which can be used to track
        variants for this test subject.
        """

        # Don't bother setting the cookie on favicon hits
        if request.path == '/favicon.ico/':
            request.exp_enabled = False
            return

        print "Key", self._app.secret_key
        exp_cookie = SecureCookie.load_cookie(request, secret_key=self._app.secret_key)
        subj_id = exp_cookie.get('id')
        print "Before request", exp_cookie, request.path
        if not subj_id:
            print "Generating new id"
            subj_id = uuid4().hex
            exp_cookie['id'] = subj_id

        request.exp_cookie = exp_cookie
        request.experiments = self.mgr.get_subject_experiments(subj_id)
        request.exp_enabled = True

        print "Before request"

    def after_request(self, response):
        if request.exp_enabled:
            print "After request", request.exp_cookie

            exp_cookie = request.exp_cookie

            if exp_cookie.should_save:
                print "Saving cookie"
                try:
                    exp_cookie.save_cookie(response)
                except Exception as e:
                    print e

        return response
