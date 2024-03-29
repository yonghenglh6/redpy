# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import translate_pb2 as translate__pb2


class TranslateStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.infer = channel.unary_unary(
                '/Translate/infer',
                request_serializer=translate__pb2.TranslateRequest.SerializeToString,
                response_deserializer=translate__pb2.TranslateReply.FromString,
                )


class TranslateServicer(object):
    """Missing associated documentation comment in .proto file."""

    def infer(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_TranslateServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'infer': grpc.unary_unary_rpc_method_handler(
                    servicer.infer,
                    request_deserializer=translate__pb2.TranslateRequest.FromString,
                    response_serializer=translate__pb2.TranslateReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Translate', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Translate(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def infer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Translate/infer',
            translate__pb2.TranslateRequest.SerializeToString,
            translate__pb2.TranslateReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
