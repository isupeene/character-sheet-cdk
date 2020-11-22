import sys

from google.protobuf import descriptor_pb2 as descriptor
from google.protobuf.compiler import plugin_pb2 as plugin


def implements_feature_source(message_type):
    has_feature_list = False
    has_name = False
    for field in [f for f in message_type.field if f.label == descriptor.FieldDescriptorProto.LABEL_REPEATED and f.type == descriptor.FieldDescriptorProto.TYPE_MESSAGE]:
        if field.type_name == ".ca.isupeene.charactersheet.cdk.Feature" and field.name == "feature":
            has_feature_list  = True
            break
    for field in [f for f in message_type.field if f.label != descriptor.FieldDescriptorProto.LABEL_REPEATED and f.type == descriptor.FieldDescriptorProto.TYPE_STRING]:
        if field.name == "name":
            has_name = True
            break
    return has_feature_list and has_name

def generate_code(request):
    response = plugin.CodeGeneratorResponse()

    for request_file in request.proto_file:
        java_file_path = "/".join(request_file.package.split(".") + [request_file.name.split("/")[-1].split(".")[0].capitalize() + ".java"])

        response_file = response.file.add()
        response_file.name = java_file_path
        response_file.insertion_point = "outer_class_scope"
        response_file.content = """
            /**
             * Any model type with a name and a list of features implements the FeatureSource interface.
             * The names are intended to be human-readable, but not necessarily unique across all feature
             * sources.
             */
            public static interface FeatureSource {
                /**
                 * The list of {@link ca.isupeene.charactersheet.cdk.Model.Feature Features} granted.
                 */
                public java.util.List<ca.isupeene.charactersheet.cdk.Model.Feature> getFeatureList();
                /**
                 * A human-readable name.
                 */
                public java.lang.String getName();
            }
        """

        for message_type in request_file.message_type:
            if implements_feature_source(message_type):
                response_file = response.file.add()
                response_file.name = java_file_path
                response_file.insertion_point = "message_implements:{}.{}".format(request_file.package, message_type.name)
                response_file.content = "FeatureSource,"
    return response

if __name__ == '__main__':
    # Parse request from stdin
    # https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/compiler/PluginProtos.CodeGeneratorRequest
    request = plugin.CodeGeneratorRequest()
    request.ParseFromString(sys.stdin.buffer.read())

    # Generate code and write to stdout
    # https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/compiler/PluginProtos.CodeGeneratorResponse
    sys.stdout.buffer.write(generate_code(request).SerializeToString())