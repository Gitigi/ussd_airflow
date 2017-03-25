from ussd.core import UssdHandlerAbstract, load_yaml
from rest_framework import serializers
from ussd.screens.serializers import NextUssdScreenSerializer
import staticconf


class VariableDefinition(serializers.Serializer):
    file = serializers.CharField()
    namespace = serializers.CharField(max_length=100)


class ValidateResposeSerialzier(serializers.Serializer):
    expression = serializers.CharField(max_length=255)


class UssdReportSessionSerializer(serializers.Serializer):
    session_key = serializers.CharField(max_length=100)
    validate_response = serializers.ListField(
        child=ValidateResposeSerialzier()
    )
    request_conf = serializers.DictField()



class InitialScreenSerializer(NextUssdScreenSerializer):
    variables = VariableDefinition(required=False)
    create_ussd_variables = serializers.DictField(default={})
    default_language = serializers.CharField(required=False,
                                             default="en")
    ussd_report_session = UssdReportSessionSerializer(required=False)



class InitialScreen(UssdHandlerAbstract):

    screen_type = "initial_screen"

    serializer = InitialScreenSerializer

    def handle(self):

        if isinstance(self.screen_content, dict):
            if self.screen_content.get('variables'):
                self.load_variable_files()

            # create ussd variables defined int the yaml
            self.create_variables()

            # set default language
            self.set_language()

            next_screen = self.screen_content['next_screen']

            # call report session
            if self.screen_content.get('ussd_report_session'):
                self.fire_ussd_report_session_task(self.initial_screen,
                                                   self.ussd_request.session_id
                                                   )
        else:
            next_screen = self.screen_content
        return self.ussd_request.forward(next_screen)

    def create_variables(self):
        for key, value in \
                self.screen_content.get('create_ussd_variables', {}). \
                        items():
            self.ussd_request.session[key] = \
                self.evaluate_jija_expression(value,
                                              lazy_evaluating=True,
                                              session=self.ussd_request.session
                                              )

    def load_variable_files(self):
        variable_conf = self.screen_content['variables']
        file_path = variable_conf['file']
        namespace = variable_conf['namespace']

        # check if it has been loaded
        if not namespace in \
                staticconf.config.configuration_namespaces:
            load_yaml(file_path, namespace)

        self.ussd_request.session.update(
            staticconf.config.configuration_namespaces[namespace].
            configuration_values
        )

    def set_language(self):
        self.ussd_request.session['default_language'] = \
            self.screen_content.get('default_language', 'en')
