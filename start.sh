#!/bin/bash
gunicorn -c gunicorn_conf.py api.app:app
