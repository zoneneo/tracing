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

import six
import socket
import struct

_max_signed_port = (1 << 15) - 1
_max_unsigned_port = (1 << 16)
_max_signed_id = (1 << 63) - 1
_max_unsigned_id = (1 << 64)

if six.PY3:
    long = int

class TagType(object):
  STRING = 0
  DOUBLE = 1
  BOOL = 2
  LONG = 3
  BINARY = 4

  _VALUES_TO_NAMES = {
    0: "STRING",
    1: "DOUBLE",
    2: "BOOL",
    3: "LONG",
    4: "BINARY",
  }

  _NAMES_TO_VALUES = {
    "STRING": 0,
    "DOUBLE": 1,
    "BOOL": 2,
    "LONG": 3,
    "BINARY": 4,
  }

class SpanRefType(object):
  CHILD_OF = 0
  FOLLOWS_FROM = 1

  _VALUES_TO_NAMES = {
    0: "CHILD_OF",
    1: "FOLLOWS_FROM",
  }

  _NAMES_TO_VALUES = {
    "CHILD_OF": 0,
    "FOLLOWS_FROM": 1,
  }


class Tag(object):
  def __init__(self, key=None, vType=None, vStr=None):
    self.key = key
    self.vType = vType
    self.vStr = vStr


def ipv4_to_int(ipv4):
    if ipv4 == 'localhost':
        ipv4 = '127.0.0.1'
    elif ipv4 == '::1':
        ipv4 = '127.0.0.1'
    try:
        return struct.unpack('!i', socket.inet_aton(ipv4))[0]
    except:
        return 0


def id_to_int(big_id):
    if big_id is None:
        return None
    # thrift defines ID fields as i64, which is signed,
    # therefore we convert large IDs (> 2^63) to negative longs
    if big_id > _max_signed_id:
        big_id -= _max_unsigned_id
    return big_id


def make_string_tag(key, value, max_length):
    if len(value) > max_length:
        value = value[:max_length]
    return Tag(key=key,
        vType=str,
        vStr=value,
    )

# def make_string_tag(key, value, max_length):
#     if len(value) > max_length:
#         value = value[:max_length]
#     return ttypes.Tag(
#         key=key,
#         vType=ttypes.TagType.STRING,
#         vStr=value,
#     )

def timestamp_micros(ts):
    return long(ts * 1000000)


def make_tags(tags, max_length):
    # TODO extend to support non-string tag values
    return [
        make_string_tag(key=k, value=str(v), max_length=max_length)
        for k, v in six.iteritems(tags or {})
    ]


def make_log(timestamp, fields, max_length):
    return dict(
        timestamp=timestamp_micros(ts=timestamp),
        fields=make_tags(tags=fields, max_length=max_length),
    )

# def make_log(timestamp, fields, max_length):
#     return ttypes.Log(
#         timestamp=timestamp_micros(ts=timestamp),
#         fields=make_tags(tags=fields, max_length=max_length),
#     )

# def make_process(service_name, tags, max_length):
#     return ttypes.Process(
#         serviceName=service_name,
#         tags=make_tags(tags=tags, max_length=max_length),
#     )
