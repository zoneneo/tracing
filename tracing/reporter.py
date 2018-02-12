# Copyright (c) 2016 Uber Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from builtins import object
import logging
import threading
import socket
# from concurrent.futures import Future
from .constants import DEFAULT_FLUSH_INTERVAL
from . import thrift
from .metrics import Metrics, LegacyMetricsFactory
from .utils import ErrorReporter
import json

default_logger = logging.getLogger('algo_tracing')


class NullReporter(object):
    """Ignores all spans."""
    def report_span(self, span):
        pass

    def set_process(self, service_name, tags, max_length):
        pass

    def close(self):
        # fut = Future()
        # fut.set_result(True)
        fut=None
        return fut


class InMemoryReporter(NullReporter):
    """Stores spans in memory and returns them via get_spans()."""
    def __init__(self):
        super(InMemoryReporter, self).__init__()
        self.spans = []
        self.lock = threading.Lock()

    def report_span(self, span):
        with self.lock:
            self.spans.append(span)

    def get_spans(self):
        with self.lock:
            return self.spans[:]


class LoggingReporter(NullReporter):
    """Logs all spans."""
    def __init__(self, logger=None):
        self.logger = logger if logger else default_logger

    def report_span(self, span):
        self.logger.info('Reporting span %s', span)


class Reporter(NullReporter):
    """Receives completed spans from Tracer and submits them out of process."""
    def __init__(self, channel, error_reporter=None, metrics=None, metrics_factory=None, **kwargs):
        from threading import Lock
        self.metrics_factory = metrics_factory or LegacyMetricsFactory(metrics or Metrics())
        self.metrics = ReporterMetrics(self.metrics_factory)
        self.error_reporter = error_reporter or ErrorReporter(Metrics())
        self.logger = kwargs.get('logger', default_logger)
        self.agent = None #Agent.Client(self._channel, self)
        self.stopped = False
        self.stop_lock = Lock()
        self._process_lock = Lock()
        self._process = None
        self._algodb = channel

    def set_process(self, service_name, tags, max_length):
        with self._process_lock:
            # self._process = thrift.make_process(
            #     service_name=service_name, tags=tags, max_length=max_length,
            # )
            self._process = (service_name, thrift.make_tags(tags=tags, max_length=max_length,))


    def report_span(self, span):
        self._submit(span)


    def _submit(self, span):
        if not span:
            return
        with self._process_lock:
            process = self._process
            if not process:
                return
        try:
            service_name=self._process[0]
            key='/%s|%s'%(service_name,span.span_id)
            self._algodb.put('%s'%key,'%s'%span)
            print key,self._process
            self.metrics.reporter_success(1)
        except Exception as e:
            print str(e)
            self.metrics.reporter_failure(1)
            self.error_reporter.error(
                'Failed to submit traces to algo-agent: %s', e)

    def _send(self, batch):
        return self.agent.emitBatch(batch)

    def close(self):
        with self.stop_lock:
            self.stopped = True


class ReporterMetrics(object):
    def __init__(self, metrics_factory):
        self.reporter_success = \
            metrics_factory.create_counter(name='algo.spans', tags={'reported': 'true'})
        self.reporter_failure = \
            metrics_factory.create_counter(name='algo.spans', tags={'reported': 'false'})
        self.reporter_dropped = \
            metrics_factory.create_counter(name='algo.spans', tags={'dropped': 'true'})
        self.reporter_socket = \
            metrics_factory.create_counter(name='algo.spans', tags={'socket_error': 'true'})

