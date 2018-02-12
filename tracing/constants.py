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

from __future__ import absolute_import, unicode_literals, print_function

from . import __version__

import six

# Max number of bits to use when generating random ID
MAX_ID_BITS = 64

# How often remotely controller sampler polls for sampling strategy
DEFAULT_SAMPLING_INTERVAL = 60

# How often remote reporter does a preemptive flush of its buffers
DEFAULT_FLUSH_INTERVAL = 1

# Name of the HTTP header used to encode trace ID
TRACE_ID_HEADER = 'algo-trace-id' if six.PY3 else b'algo-trace-id'

# Prefix for HTTP headers used to record baggage items
BAGGAGE_HEADER_PREFIX = 'algoctx-' if six.PY3 else b'algoctx-'

# The name of HTTP header or a TextMap carrier key which, if found in the
# carrier, forces the trace to be sampled as "debug" trace. The value of the
# header is recorded as the tag on the # root span, so that the trace can
# be found in the UI using this value as a correlation ID.
DEBUG_ID_HEADER_KEY = 'algo-debug-id'

ALGO_CLIENT_VERSION = 'Python-%s' % __version__

# Tracer-scoped tag that tells the version of Algo client library
ALGO_VERSION_TAG_KEY = 'algo.version'

# Tracer-scoped tag that contains the hostname
ALGO_HOSTNAME_TAG_KEY = 'algo.hostname'

# the type of sampler that always makes the same decision.
SAMPLER_TYPE_CONST = 'const'

# the type of sampler that polls Algo agent for sampling strategy.
SAMPLER_TYPE_REMOTE = 'remote'

# the type of sampler that samples traces with a certain fixed probability.
SAMPLER_TYPE_PROBABILISTIC = 'probabilistic'

# the type of sampler that samples only up to a fixed number
# of traces per second.
# noinspection SpellCheckingInspection
SAMPLER_TYPE_RATE_LIMITING = 'ratelimiting'

# the type of sampler that samples only up to a fixed number
# of traces per second.
# noinspection SpellCheckingInspection
SAMPLER_TYPE_LOWER_BOUND = 'lowerbound'

# max length for tag values. Longer values will be truncated.
MAX_TAG_VALUE_LENGTH = 1024

# Constant for sampled flag
SAMPLED_FLAG = 0x01

# Constant for debug flag
DEBUG_FLAG = 0x02


DATABASE_HOST_KEY = 'db.host'

DATABASE_PORT_KEY= 'db.port'

#
ALGO_AUTH_KEY = 'auth'

ALGO_BACKEND_KEY = 'backend'

ALGO_MONITOR_KEY = 'monitor' 

ALGO_SCHED_KEY = 'scheduler'

ALGO_AGENT_KEY = 'agent'

# SERVICE_PORT = {
#     ALGO_BACKEND_KEY : 5000
#     ALGO_AUTH_KEY : 8000
#     ALGO_MONITOR_KEY : 5010
#     ALGO_SCHED_KEY : 5020
#     ALGO_AGENT_KEY : 5030
# }

SERVICES = {
    ALGO_BACKEND_KEY : 100,
    ALGO_AUTH_KEY : 200,
    ALGO_MONITOR_KEY : 300,
    ALGO_SCHED_KEY : 400,
    ALGO_AGENT_KEY : 600,
}

METHODS ={
    'version':'0.0.1',
    'auth':[
        'RegisterUser',
        'AuthorizeUser',
    ]
}