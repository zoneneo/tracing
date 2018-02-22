from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()  # noqa

from builtins import object
from past.builtins import basestring

from opentracing import (
    InvalidCarrierException,
    SpanContextCorruptedException,
)
from .constants import (
    BAGGAGE_HEADER_PREFIX,
    DEBUG_ID_HEADER_KEY,
    TRACE_ID_HEADER,
)
from .span_context import SpanContext
from .constants import SAMPLED_FLAG, DEBUG_FLAG

import six
import urllib.parse


class Codec(object):
    def inject(self, span_context, carrier):
        raise NotImplementedError()

    def extract(self, carrier):
        raise NotImplementedError()


class TextCodec(Codec):
    def __init__(self,
                 url_encoding=False,
                 trace_id_header=TRACE_ID_HEADER,
                 baggage_header_prefix=BAGGAGE_HEADER_PREFIX,
                 debug_id_header=DEBUG_ID_HEADER_KEY):
        self.url_encoding = url_encoding
        self.trace_id_header = trace_id_header.lower().replace('_', '-')
        self.baggage_prefix = baggage_header_prefix.lower().replace('_', '-')
        self.debug_id_header = debug_id_header.lower().replace('_', '-')
        self.prefix_length = len(baggage_header_prefix)

    def inject(self, span_context, carrier):
        if not isinstance(carrier, dict):
            raise InvalidCarrierException('carrier not a collection')
        carrier[self.trace_id_header] = span_context_to_string(
            trace_id=span_context.trace_id, span_id=span_context.span_id,
            parent_id=span_context.parent_id, flags=span_context.flags)
        baggage = span_context.baggage
        if baggage:
            for key, value in six.iteritems(baggage):
                encoded_key = key
                if self.url_encoding:
                    encoded_value = urllib.parse.quote(value)
                    if six.PY2 and isinstance(key, six.text_type):
                        encoded_key = key.encode('utf-8')
                else:
                    encoded_value = value
                header_key = '%s%s' % (self.baggage_prefix, encoded_key)
                carrier[header_key] = encoded_value

    def extract(self, carrier):
        if not hasattr(carrier, 'items'):
            raise InvalidCarrierException('carrier not a collection')
        trace_id, span_id, parent_id, flags = None, None, None, None
        baggage = None
        debug_id = None
        for key, value in six.iteritems(carrier):
            uc_key = key.lower()
            if uc_key == self.trace_id_header:
                if self.url_encoding:
                    value = urllib.parse.unquote(value)
                trace_id, span_id, parent_id, flags = \
                    span_context_from_string(value)
            elif uc_key.startswith(self.baggage_prefix):
                if self.url_encoding:
                    value = urllib.parse.unquote(value)
                attr_key = key[self.prefix_length:]
                if baggage is None:
                    baggage = {attr_key.lower(): value}
                else:
                    baggage[attr_key.lower()] = value
            elif uc_key == self.debug_id_header:
                if self.url_encoding:
                    value = urllib.parse.unquote(value)
                debug_id = value
        if not trace_id and baggage:
            raise SpanContextCorruptedException('baggage without trace ctx')
        if not trace_id:
            if debug_id is not None:
                return SpanContext.with_debug_id(debug_id=debug_id)
            return None
        return SpanContext(trace_id=trace_id, span_id=span_id,
                           parent_id=parent_id, flags=flags,
                           baggage=baggage)


class BinaryCodec(Codec):
    def __init__(self, trace_id_header=TRACE_ID_HEADER):
        self.trace_id_header = trace_id_header.lower().replace('_', '-')

    def inject(self, span_context, carrier):
        if not isinstance(carrier, bytearray):
            raise InvalidCarrierException('carrier not a bytearray')

        baggage = span_context.baggage.copy()
        baggage[self.trace_id_header] = span_context_to_string(
            trace_id=span_context.trace_id, span_id=span_context.span_id,
            parent_id=span_context.parent_id, flags=span_context.flags)
        bin_baggage = bytearray(json.dumps(baggage))
        carrier.extend(bytearray(struct.pack("I", len(bin_baggage))))
        carrier.extend(bin_baggage)

    def extract(self, carrier):
        if not isinstance(carrier, bytearray):
            raise InvalidCarrierException('carrier not a bytearray')

        ctx_len = struct.unpack('I', carrier[0:4])[0]
        carrier = json.loads(str(carrier[4:4 + ctx_len]))
        trace_id, span_id, parent_id, flags = None, None, None, None
        baggage = None
        for key, value in six.iteritems(carrier):
            uc_key = key.lower()
            if uc_key == self.trace_id_header:
                trace_id, span_id, parent_id, flags = \
                    span_context_from_string(value)
            else:
                if baggage is None:
                    baggage = {uc_key: value}
                else:
                    baggage[uc_key] = value

        if baggage == None or (not isinstance(baggage, dict)):
            raise SpanContextCorruptedException()

        return SpanContext(trace_id=trace_id, span_id=span_id,
                           parent_id=parent_id, flags=flags,
                           baggage=baggage)


def span_context_to_string(trace_id, span_id, parent_id, flags):
    """
    Serialize span ID to a string
        {trace_id}:{span_id}:{parent_id}:{flags}

    Numbers are encoded as variable-length lower-case hex strings.
    If parent_id is None, it is written as 0.

    :param trace_id:
    :param span_id:
    :param parent_id:
    :param flags:
    """
    parent_id = parent_id or 0
    return '{:x}:{:x}:{:x}:{:x}'.format(trace_id, span_id, parent_id, flags)


def span_context_from_string(value):
    """
    Decode span ID from a string into a TraceContext.
    Returns None if the string value is malformed.

    :param value: formatted {trace_id}:{span_id}:{parent_id}:{flags}
    """
    if type(value) is list and len(value) > 0:
        # sometimes headers are presented as arrays of values
        if len(value) > 1:
            raise SpanContextCorruptedException(
                'trace context must be a string or array of 1: "%s"' % value)
        value = value[0]
    if not isinstance(value, basestring):
        raise SpanContextCorruptedException(
            'trace context not a string "%s"' % value)
    parts = value.split(':')
    if len(parts) != 4:
        raise SpanContextCorruptedException(
            'malformed trace context "%s"' % value)
    try:
        trace_id = int(parts[0], 16)
        span_id = int(parts[1], 16)
        parent_id = int(parts[2], 16)
        flags = int(parts[3], 16)
        if trace_id < 1 or span_id < 1 or parent_id < 0 or flags < 0:
            raise SpanContextCorruptedException(
                'malformed trace context "%s"' % value)
        if parent_id == 0:
            parent_id = None
        return trace_id, span_id, parent_id, flags
    except ValueError as e:
        raise SpanContextCorruptedException(
            'malformed trace context "%s": %s' % (value, e))


def header_to_hex(header):
    if not isinstance(header, (str, six.text_type)):
        raise SpanContextCorruptedException(
            'malformed trace context "%s", expected hex string' % header)

    try:
        return int(header, 16)
    except ValueError:
        raise SpanContextCorruptedException(
            'malformed trace context "%s", expected hex string' % header)
